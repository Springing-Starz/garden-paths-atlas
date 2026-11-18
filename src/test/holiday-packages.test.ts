import { describe, expect, it } from 'vitest';
import { findMoreDocumentsRepo } from '@/data/more-documents';
import { loadRepositoryDocuments } from '@/lib/repository-catalog';
import type { ClassHubData } from '@/lib/class-hubs';

const hubs = import.meta.glob<{ default: ClassHubData }>('@/data/class-hubs/*.json', { eager: true });

describe('Holiday Packages', () => {
  it('opens the packages documents page from every class Holiday Packages button', () => {
    for (const hub of Object.values(hubs)) {
      const menu = hub.default.menus.find(item => item.label === 'HOLIDAY PACKAGES');
      if (!menu) continue;
      expect(menu.href).toBe('/more/packages');
      expect(menu.items).toEqual([]);
    }
  });
  it('has an empty packages catalog while the repository is empty', async () => {
    expect(findMoreDocumentsRepo('packages')?.label).toBe('Holiday Packages');
    expect(await loadRepositoryDocuments('packages')).toEqual([]);
  });
});
