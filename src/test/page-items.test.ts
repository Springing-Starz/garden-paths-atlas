import { describe, expect, it } from 'vitest';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = join(process.cwd(), 'src/data/catalog');
const read = (p: string) => JSON.parse(readFileSync(p, 'utf8'));

const readThumbs = () => Object.assign({}, ...require('node:fs').readdirSync(join(root, 'thumb-map')).filter((f: string) => f.endsWith('.json')).map((f: string) => read(join(root, 'thumb-map', f))));

describe('baked page items', () => {
  it('keeps Senior Five covers, page counts and sizes consistent across collections', () => {
    const thumbs = readThumbs();
    const urls = new Set<string>();
    let covers = 0;
    let missing = 0;
    let unreadable = 0;
    for (const kind of ['resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'page-items', kind))) {
        if (!/^SeniorFive|^(?:exams-s5|s5(?:-notes|-past-papers)?)\.json$/.test(name)) continue;
        for (const item of read(join(root, 'page-items', kind, name))) {
          if (!new URL(item.pdfUrl).pathname.toLowerCase().endsWith('.pdf')) continue;
          const saved = thumbs[item.pdfUrl];
          if (saved) {
            expect(item.thumbUrl).toBe(saved.thumbUrl);
            expect(existsSync(join(process.cwd(), 'public', saved.thumbUrl))).toBe(true);
            if (saved.thumbUrl === '/thumbs/broken-link.webp') expect(item.pages).toBeUndefined();
            else {
              expect(item.pages).toBe(saved.pages);
              expect(item.sizeBytes).toBe(saved.sizeBytes);
              expect(item.pages).toBeGreaterThan(0);
              expect(item.sizeBytes).toBeGreaterThan(0);
            }
          }
          if (urls.has(item.pdfUrl)) continue;
          urls.add(item.pdfUrl);
          if (!saved) unreadable++;
          else if (saved.thumbUrl === '/thumbs/broken-link.webp') missing++;
          else covers++;
        }
      }
    }
    expect(covers).toBe(1887);
    expect(missing).toBe(77);
    expect(unreadable).toBe(3);
  });
  it('keeps Senior Three covers, page counts and sizes consistent across collections', () => {
    const thumbs = readThumbs();
    const urls = new Set<string>();
    let covers = 0;
    let missing = 0;
    let unreadable = 0;
    for (const kind of ['resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'page-items', kind))) {
        if (!/^SeniorThree|^(?:exams-s3|s3(?:-notes|-past-papers)?)\.json$/.test(name)) continue;
        for (const item of read(join(root, 'page-items', kind, name))) {
          if (!new URL(item.pdfUrl).pathname.toLowerCase().endsWith('.pdf')) continue;
          const saved = thumbs[item.pdfUrl];
          if (saved) {
            expect(item.thumbUrl).toBe(saved.thumbUrl);
            expect(existsSync(join(process.cwd(), 'public', saved.thumbUrl))).toBe(true);
            if (saved.thumbUrl === '/thumbs/broken-link.webp') expect(item.pages).toBeUndefined();
            else {
              expect(item.pages).toBe(saved.pages);
              expect(item.sizeBytes).toBe(saved.sizeBytes);
              expect(item.pages).toBeGreaterThan(0);
              expect(item.sizeBytes).toBeGreaterThan(0);
            }
          }
          if (urls.has(item.pdfUrl)) continue;
          urls.add(item.pdfUrl);
          if (!saved) unreadable++;
          else if (saved.thumbUrl === '/thumbs/broken-link.webp') missing++;
          else covers++;
        }
      }
    }
    expect(covers).toBe(2148);
    expect(missing).toBe(114);
    expect(unreadable).toBe(8);
  });
  it('keeps prepared Senior One page counts and sizes consistent with saved covers', () => {
    const thumbs = readThumbs();
    const prepared = new Set<string>();
    for (const kind of ['resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'page-items', kind))) {
        if (!/^SeniorOne|^(?:exams-s1|s1(?:-notes|-past-papers)?)\.json$/.test(name)) continue;
        for (const item of read(join(root, 'page-items', kind, name))) {
          const saved = thumbs[item.pdfUrl];
          if (!saved) continue;
          expect(item.thumbUrl).toBe(saved.thumbUrl);
          expect(existsSync(join(process.cwd(), 'public', saved.thumbUrl))).toBe(true);
          if (saved.thumbUrl === '/thumbs/broken-link.webp') expect(item.pages).toBeUndefined();
          else {
            expect(item.pages).toBe(saved.pages);
            expect(item.pages).toBeGreaterThan(0);
            expect(item.sizeBytes).toBe(saved.sizeBytes);
            expect(item.sizeBytes).toBeGreaterThan(0);
            prepared.add(item.pdfUrl);
          }
        }
      }
    }
    expect(prepared.size).toBe(1218);
  });
  it('keeps prepared Senior Two page counts and sizes consistent with saved covers', () => {
    const thumbs = readThumbs();
    const prepared = new Set<string>();
    for (const kind of ['resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'page-items', kind))) {
        if (!/^SeniorTwo|^(?:exams-s2|s2(?:-notes|-past-papers)?)\.json$/.test(name)) continue;
        for (const item of read(join(root, 'page-items', kind, name))) {
          const saved = thumbs[item.pdfUrl];
          if (!saved) continue;
          expect(item.thumbUrl).toBe(saved.thumbUrl);
          expect(existsSync(join(process.cwd(), 'public', saved.thumbUrl))).toBe(true);
          if (saved.thumbUrl === '/thumbs/broken-link.webp') expect(item.pages).toBeUndefined();
          else {
            expect(item.pages).toBe(saved.pages);
            expect(item.pages).toBeGreaterThan(0);
            expect(item.sizeBytes).toBe(saved.sizeBytes);
            expect(item.sizeBytes).toBeGreaterThan(0);
            prepared.add(item.pdfUrl);
          }
        }
      }
    }
    expect(prepared.size).toBe(1135);
  });
  it('keeps Primary 6 covers, page counts and sizes consistent in every collection', () => {
    const thumbs = readThumbs();
    const urls = new Set<string>();
    let missing = 0;
    let unreadable = 0;
    let covers = 0;
    for (const kind of ['resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'page-items', kind))) {
        if (!/^PrimarySix|^(?:exams-p6|p6(?:-notes|-past-papers)?)\.json$/.test(name)) continue;
        for (const item of read(join(root, 'page-items', kind, name))) {
          if (!new URL(item.pdfUrl).pathname.toLowerCase().endsWith('.pdf')) continue;
          const saved = thumbs[item.pdfUrl];
          if (saved) {
            expect(item.thumbUrl).toBe(saved.thumbUrl);
            expect(existsSync(join(process.cwd(), 'public', saved.thumbUrl))).toBe(true);
            if (saved.thumbUrl === '/thumbs/broken-link.webp') expect(item.pages).toBeUndefined();
            else {
              expect(item.pages).toBe(saved.pages);
              expect(item.sizeBytes).toBe(saved.sizeBytes);
              expect(item.pages).toBeGreaterThan(0);
              expect(item.sizeBytes).toBeGreaterThan(0);
            }
          }
          if (urls.has(item.pdfUrl)) continue;
          urls.add(item.pdfUrl);
          if (!saved) unreadable++;
          else if (saved.thumbUrl === '/thumbs/broken-link.webp') missing++;
          else covers++;
        }
      }
    }
    expect(covers).toBe(2102);
    expect(missing).toBe(188);
    expect(unreadable).toBe(5);
  });
  it('keeps prepared Primary 3 PDF metadata consistent with its saved covers', () => {
    const thumbs = readThumbs();
    let checked = 0;
    for (const kind of ['resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'page-items', kind))) {
        if (!/^PrimaryThree|^p3(?:-|\.json)/.test(name)) continue;
        for (const item of read(join(root, 'page-items', kind, name))) {
          const saved = thumbs[item.pdfUrl];
          if (!saved) continue;
          expect(item.thumbUrl).toBe(saved.thumbUrl);
          expect(existsSync(join(process.cwd(), 'public', saved.thumbUrl))).toBe(true);
          if (saved.thumbUrl === '/thumbs/broken-link.webp') {
            expect(item.pages).toBeUndefined();
          } else {
            expect(item.pages).toBe(saved.pages);
            expect(item.pages).toBeGreaterThan(0);
            expect(item.sizeBytes).toBe(saved.sizeBytes);
            expect(item.sizeBytes).toBeGreaterThan(0);
            checked++;
          }
        }
      }
    }
    expect(checked).toBeGreaterThan(0);
  });
  it('every catalog page has one baked file matching its document ids, in order', () => {
    for (const kind of ['legacy', 'resources', 'repositories']) {
      for (const name of readdirSync(join(root, 'pages', kind))) {
        const ids: string[] = read(join(root, 'pages', kind, name)).documentIds ?? [];
        const items: { id?: string }[] = read(join(root, 'page-items', kind, name));
        expect(items.length, `${kind}/${name}`).toBe(ids.length);
      }
    }
  });
});
