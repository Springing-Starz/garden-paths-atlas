import { DocumentsSkeleton } from '@/components/documents-skeleton';
import { MenuSkeleton, menuVariantFor } from '@/components/menu-skeleton';
import { createFileRoute, notFound, redirect, useRouterState } from '@tanstack/react-router';
import { ResourcePage } from '@/components/resource-page';
import manifest from '@/data/resource-manifest.json';
import type { ResourcePageData } from '@/lib/resources';
import { lazy, Suspense } from 'react';
import legacyManifest from '@/data/legacy/manifest.json';
import type { LegacyPageData } from '@/lib/legacy-pages';
import type { StaticPage } from '@/lib/static-catalog';
import { isDocumentFile } from '@/lib/document-formats';
import type { ResourceRecord } from '@/lib/resources';
import { useRouteStylesheets, warmRouteStylesheets } from '@/lib/route-stylesheets';
import { MORE_DOCUMENTS, moreDocumentsClass } from '@/data/more-documents';
import { ClassHub } from '@/components/class-hub';
import type { ClassHubData } from '@/lib/class-hubs';

const moreFor = (path: string) => { const key = moreDocumentsClass(path); return key ? MORE_DOCUMENTS[key] : undefined; };
const LegacyPage = lazy(() => import('@/components/legacy-page').then(module => ({ default: module.LegacyPage })));

const resourceStylesheets = ['bootstrap.min.css', 'font-awesome.css', 'flipbook.style.css', 'footer.css'].map(file => `/resource-source/css/${file}`);

const pages = import.meta.glob<{ default: StaticPage<ResourcePageData> }>('../data/catalog/pages/resources/*.json');
const legacyPages = import.meta.glob<{ default: StaticPage<LegacyPageData> }>('../data/catalog/pages/legacy/*.json');
const legacyItems = import.meta.glob<{ default: ResourceRecord[] }>('../data/catalog/page-items/legacy/*.json');
const resourceItems = import.meta.glob<{ default: ResourceRecord[] }>('../data/catalog/page-items/resources/*.json');
const fragmentFiles = import.meta.glob<{ default: string }>('../data/legacy/fragments/*.json');
const classHubs = import.meta.glob<{ default: ClassHubData }>('../data/class-hubs/*.json', { eager: true });

// Each page's documents are pre-baked into one file (scripts/bake_page_items.py), so a page costs one small request.
async function hydratePage<T extends { items: ResourceRecord[] }>(page: StaticPage<T>, load?: () => Promise<{ default: ResourceRecord[] }>) {
  if (!load) throw notFound();
  const { documentIds: _ids, ...rest } = page;
  const items = (await load()).default.filter(item => isDocumentFile(item.pdfUrl));
  return { ...rest, items } as unknown as T & { recoverySource?: string };
}

export const Route = createFileRoute('/$')({
  staticData: { sitemap: true },
  loader: async ({ params }) => {
    const path = (params._splat ?? '').replace(/\/+$/, '');
    if (path === 'index.html') throw redirect({ to: '/', statusCode: 301 });
    const hub = classHubs[`../data/class-hubs/${path}.json`];
    if (hub) return { path, kind: 'hub' as const, data: hub.default };
    const entry = manifest[path as keyof typeof manifest];
    if (!entry) {
      const legacy = legacyManifest[path as keyof typeof legacyManifest];
      if (!legacy) throw notFound();
      const load = legacyPages[`../data/catalog/pages/legacy/${legacy.data}`];
      if (!load) throw notFound();
      const page = (await load()).default;
      const fragments: Record<string, string> = {};
      const read = async (key: string): Promise<void> => {
        if (key in fragments) return;
        const get = fragmentFiles[`../data/legacy/fragments/${key}.json`];
        if (!get) throw notFound();
        const text = (await get()).default;
        fragments[key] = text;
        await Promise.all(Array.from(text.matchAll(/data-key="([^"]+)"/g), match => read(match[1] ?? '')));
      };
      // Warm CSS independently: slow stylesheets must not hold back document data.
      void warmRouteStylesheets(page.links);
      const [data] = await Promise.all([
        hydratePage<LegacyPageData>(page, legacyItems[`../data/catalog/page-items/legacy/${legacy.data}`]),
        Promise.all([read(page.template), read(page.styles)]),
      ]);
      return { path, kind: 'legacy' as const, data, fragments };
    }
    const load = pages[`../data/catalog/pages/resources/${entry.data}`];
    if (!load) throw notFound();
    void warmRouteStylesheets(resourceStylesheets);
    const data = await load().then(module => hydratePage<ResourcePageData>(module.default, resourceItems[`../data/catalog/page-items/resources/${entry.data}`]));
    return { path, kind: 'resource' as const, data };
  },
  // The catalog is static, so loaded pages never go stale; back/forward and hover-preloaded pages skip the skeleton.
  staleTime: Infinity,
  preloadStaleTime: Infinity,
  head: ({ loaderData }) => {
    const pageTitle = loaderData?.data.title ?? 'Resource unavailable | Fresh Teacher';
    const title = pageTitle.includes('Fresh Teacher') ? pageTitle : `${pageTitle} | Fresh Teacher`;
    const description = loaderData?.data.description ?? 'The requested Fresh Teacher resource page is unavailable.';
    return { meta: [
      { title }, { name: 'description', content: description },
      { property: 'og:title', content: title }, { property: 'og:description', content: description },
      { property: 'og:type', content: 'website' }, { name: 'twitter:card', content: 'summary_large_image' },
      ...(!loaderData ? [{ name: 'robots', content: 'noindex' }] : []),
    ], links: loaderData ? (loaderData.kind === 'hub' ? [] : loaderData.kind === 'legacy' ? loaderData.data.links : resourceStylesheets).map(href => ({ rel: 'stylesheet', href })) : [] };
  },
  pendingComponent: PageSkeleton,
  component: LegacyResource,
});

function PageSkeleton() {
  const pathname = useRouterState({ select: state => state.location.pathname });
  const path = pathname.replace(/^\/+|\/+$/g, '');
  const hub = classHubs[`../data/class-hubs/${path}.json`];
  if (hub) return <ClassHub key={path} data={hub.default} />;
  const entry = legacyManifest[path as keyof typeof legacyManifest];
  return entry?.count === 0 ? <MenuSkeleton variant={menuVariantFor(path)} /> : <DocumentsSkeleton />;
}

function LegacyResource() {
  const result = Route.useLoaderData();
  // Retain route isolation without making stylesheet readiness a content gate.
  useRouteStylesheets(result.kind === 'hub' ? [] : result.kind === 'legacy' ? result.data.links : resourceStylesheets);
  const page = result.kind === 'hub' ? <ClassHub key={result.path} data={result.data} /> : result.kind === 'legacy'
    ? <LegacyPage key={result.path} data={result.data} fragments={result.fragments} moreDocuments={moreFor(result.path)} />
    : <ResourcePage key={result.path} data={result.data} />;
  return (
    <>
      <div className="route-fade route-fade--in"><Suspense fallback={<PageSkeleton />}>{page}</Suspense></div>
    </>
  );
}
