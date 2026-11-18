"""Bake each catalog page's documents into one file so a page loads with a single request.
Run after any catalog rebuild: python3 scripts/bake_page_items.py
Optional --size-map accepts a JSON object of source URL -> byte count, collected
offline from repository blob metadata. Optional --thumb-map (from generate_thumbnails.py) adds thumbUrl and pages.
No remote requests occur while baking."""
import argparse, json, pathlib

def bake(root, size_map=None, thumb_map=None):
    sizes = size_map or {}
    thumbs = thumb_map or {}
    if any(type(value) is not int or value < 0 for value in sizes.values()):
        raise ValueError('Size metadata must contain nonnegative integer byte counts')
    shards = {p.stem: json.loads(p.read_text()) for p in (root / 'documents').glob('*.json')}
    # Persist supplied metadata in the canonical shards too, so search and
    # collection pages receive the same values after the next catalog rebuild.
    for stem, records in shards.items():
        changed = False
        for record in records.values():
            value = sizes.get(record['pdfUrl'], (thumbs.get(record['pdfUrl']) or {}).get('sizeBytes'))
            if value is not None and record.get('sizeBytes') != value:
                record['sizeBytes'] = value
                changed = True
            thumb = thumbs.get(record['pdfUrl'])
            if thumb and (record.get('thumbUrl'), record.get('pages')) != (thumb['thumbUrl'], thumb.get('pages')):
                record['thumbUrl'] = thumb['thumbUrl']
                if thumb.get('pages'): record['pages'] = thumb['pages']
                changed = True
        if changed:
            (root / 'documents' / f'{stem}.json').write_text(json.dumps(records, separators=(',', ':'), ensure_ascii=False))
    total = 0
    for kind in ('legacy', 'resources', 'repositories'):
        out = root / 'page-items' / kind
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob('*.json'): old.unlink()
        for page in (root / 'pages' / kind).glob('*.json'):
            ids = json.loads(page.read_text()).get('documentIds', [])
            items = []
            for i in ids:
                rec = shards.get(i[:2], {}).get(i)
                if rec is None: raise ValueError(f'Missing static document {i} in {page}')
                items.append(rec)
            (out / page.name).write_text(json.dumps(items, separators=(',', ':'), ensure_ascii=False))
            total += 1
    return total

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size-map', type=pathlib.Path)
    parser.add_argument('--thumb-map', type=pathlib.Path)
    args = parser.parse_args()
    sizes = json.loads(args.size_map.read_text()) if args.size_map else {}
    thumbs = {}
    if args.thumb_map and args.thumb_map.is_dir():
        for f in sorted(args.thumb_map.glob('*.json')): thumbs.update(json.loads(f.read_text()))
    elif args.thumb_map: thumbs = json.loads(args.thumb_map.read_text())
    root = pathlib.Path(__file__).resolve().parent.parent / 'src/data/catalog'
    print('baked', bake(root, sizes, thumbs), 'pages')
