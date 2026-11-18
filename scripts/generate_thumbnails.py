"""Pre-bake first-page covers and page counts for catalog PDFs.
Usage: python scripts/generate_thumbnails.py --match p7 --batch-size 1000 --offset 0 --workers 4
Resumable: existing thumbnails are skipped. Writes public/thumbs/<id>.webp and
src/data/catalog/thumb-map/<0-f>.json (url -> {thumbUrl, pages}). Then run
python scripts/bake_page_items.py --thumb-map src/data/catalog/thumb-map"""
import argparse, hashlib, io, json, pathlib, urllib.parse, urllib.request
import multiprocessing as mp, os
import urllib.error
import pypdfium2 as pdfium

# Shared cover for source links that return 404 (no pages count).
BROKEN = {'thumbUrl': '/thumbs/broken-link.webp'}

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / 'src/data/catalog'
OUT = ROOT / 'public/thumbs'
MAP = CATALOG / 'thumb-map'  # sharded by sha1(url)[0] to stay under file-size limits

def thumb_id(url): return hashlib.sha1(url.encode()).hexdigest()[:16]

def target_urls(match):
    urls = set()
    for f in (CATALOG / 'page-items').glob('*/*.json'):
        hit = not match or any(m in f.stem.lower() for m in match)
        for r in json.loads(f.read_text()):
            if not hit and not any(m in r['pdfUrl'].lower() for m in match): continue
            if urllib.parse.urlparse(r['pdfUrl']).path.lower().endswith('.pdf'): urls.add(r['pdfUrl'])
    return sorted(urls)

def fetch(url):
    parts = urllib.parse.urlsplit(url)
    safe = urllib.parse.urlunsplit(parts._replace(path=urllib.parse.quote(urllib.parse.unquote(parts.path))))
    with urllib.request.urlopen(urllib.request.Request(safe, headers={'User-Agent': 'thumb-baker'}), timeout=60) as r:
        return r.read()

def bake(url):
    name = f'{thumb_id(url)}.webp'
    data = fetch(url)
    pdf = pdfium.PdfDocument(data)
    try:
        pages = len(pdf)
        page = pdf[0]
        image = page.render(scale=240 / page.get_width()).to_pil().convert('RGB')
        buf = io.BytesIO(); image.save(buf, 'WEBP', quality=70, method=6)
        (OUT / name).write_bytes(buf.getvalue())
    finally:
        pdf.close()
    return {'thumbUrl': f'/thumbs/{name}', 'pages': pages, 'sizeBytes': len(data)}

def work(url):
    # Runs in its own process: pdfium is not thread-safe.
    try: return url, bake(url)
    except urllib.error.HTTPError as e: return url, (BROKEN if e.code == 404 else None)
    except urllib.error.URLError: return url, BROKEN
    except pdfium.PdfiumError: return url, {**BROKEN, 'locked': True}
    except Exception: return url, None

def save(done):
    MAP.mkdir(parents=True, exist_ok=True); shards = {}
    for k, v in done.items(): shards.setdefault(hashlib.sha1(k.encode()).hexdigest()[0], {})[k] = v
    for h, m in shards.items():
        tmp = MAP / f'{h}.json.tmp'
        tmp.write_text(json.dumps(m, indent=0, sort_keys=True)); os.replace(tmp, MAP / f'{h}.json')

def load_map(path=MAP):
    path = pathlib.Path(path); out = {}
    if path.is_dir():
        for f in sorted(path.glob('*.json')): out.update(json.loads(f.read_text()))
    elif path.exists(): out = json.loads(path.read_text())
    return out

def pending(done, urls):
    def ok(u):
        v = done.get(u)
        if not v: return False
        if v.get('thumbUrl') == BROKEN['thumbUrl']: return True
        return 'sizeBytes' in v and (ROOT / 'public' / v['thumbUrl'].lstrip('/')).exists()
    return [u for u in urls if not ok(u)]

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--match', default='')
    p.add_argument('--batch-size', '--limit', dest='batch', type=int, default=0)
    p.add_argument('--offset', type=int, default=0)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--status', action='store_true', help='only report progress')
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    done = load_map()
    urls = target_urls([m for m in a.match.lower().split(',') if m])
    todo = pending(done, urls)
    print(f'{a.match or "all"}: {len(urls) - len(todo)}/{len(urls)} done, {len(todo)} remaining')
    if a.status: raise SystemExit
    todo = todo[a.offset:]
    if a.batch: todo = todo[:a.batch]
    failed = 0
    with mp.Pool(a.workers, maxtasksperchild=50) as pool:
        for i, (url, meta) in enumerate(pool.imap_unordered(work, todo), 1):
            if meta: done[url] = meta
            if not meta or meta.get('thumbUrl') == BROKEN['thumbUrl']: failed += 1
            if i % 25 == 0: save(done); print(f'  {i}/{len(todo)}', flush=True)
    save(done)
    print(f'baked {len(todo) - failed}, failed/broken {failed}, total {len(done)}')
