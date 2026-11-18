"""Pre-bake first-page covers and page counts for catalog PDFs.
Usage: python scripts/generate_thumbnails.py --match baby,middle,top
Resumable: existing thumbnails are skipped. Writes public/thumbs/<id>.webp and
src/data/catalog/thumb-map.json (url -> {thumbUrl, pages}). Then run
python scripts/bake_page_items.py --thumb-map src/data/catalog/thumb-map.json"""
import argparse, hashlib, io, json, pathlib, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.error
import pypdfium2 as pdfium

# Shared cover for source links that return 404 (no pages count).
BROKEN = {'thumbUrl': '/thumbs/broken-link.webp'}

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / 'src/data/catalog'
OUT = ROOT / 'public/thumbs'
MAP = CATALOG / 'thumb-map.json'

def thumb_id(url): return hashlib.sha1(url.encode()).hexdigest()[:16]

def target_urls(match):
    urls = set()
    for f in (CATALOG / 'page-items').glob('*/*.json'):
        if match and not any(m in f.stem.lower() for m in match): continue
        for r in json.loads(f.read_text()):
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

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--match', default='')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--workers', type=int, default=1)  # pdfium is not thread-safe
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    done = json.loads(MAP.read_text()) if MAP.exists() else {}
    todo = [u for u in target_urls([m for m in a.match.lower().split(',') if m]) if u not in done or (done[u] != BROKEN and 'sizeBytes' not in done[u]) or not (ROOT / 'public' / done[u]['thumbUrl'].lstrip('/')).exists()]
    if a.limit: todo = todo[:a.limit]
    failed = 0
    with ThreadPoolExecutor(a.workers) as pool:
        jobs = {pool.submit(bake, u): u for u in todo}
        for i, job in enumerate(as_completed(jobs), 1):
            try: done[jobs[job]] = job.result()
            except urllib.error.HTTPError as e:
                if e.code == 404: done[jobs[job]] = BROKEN
                failed += 1
            except Exception: failed += 1
            if i % 50 == 0: MAP.write_text(json.dumps(done, indent=0, sort_keys=True))
    MAP.write_text(json.dumps(done, indent=0, sort_keys=True))
    print(f'baked {len(todo) - failed}, failed {failed}, total {len(done)}')
