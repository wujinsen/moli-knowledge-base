import crosslinksData from '../data/红楼梦.crosslinks.json';
import { loadBookItems, type ItemEntry } from './items';

export type ItemRef = { id: string; name: string; kind: ItemEntry['kind'] };

const crosslinks = crosslinksData as {
  book: string;
  location_items: Record<string, string[]>;
  occupant_items: Record<string, string[]>;
};

export function parseChapterNumber(text: string): number | null {
  const m = text.match(/第(\d+)回/);
  return m ? Number(m[1]) : null;
}

export function chaptersFromAppearIn(appearIn: string[] = []): number[] {
  const nums = appearIn.map(parseChapterNumber).filter((n): n is number => n != null);
  return [...new Set(nums)].sort((a, b) => a - b);
}

async function itemIndex(book: string): Promise<Map<string, ItemRef>> {
  const items = await loadBookItems(book);
  return new Map(
    items.map(({ kind, entry }) => [
      entry.data.id,
      { id: entry.data.id, name: entry.data.name, kind },
    ])
  );
}

function resolveIds(ids: string[], index: Map<string, ItemRef>): ItemRef[] {
  const out: ItemRef[] = [];
  const seen = new Set<string>();
  for (const id of ids) {
    const ref = index.get(id);
    if (ref && !seen.has(id)) {
      seen.add(id);
      out.push(ref);
    }
  }
  return out;
}

/** 地点页：相关名物（交叉表 + 实体 location 字段 + 居住者名物） */
export async function relatedItemsForPlace(
  book: string,
  placeId: string,
  occupants: string[] = []
): Promise<ItemRef[]> {
  if (book !== crosslinks.book) return [];

  const index = await itemIndex(book);
  const ids = new Set<string>();

  for (const id of crosslinks.location_items[placeId] ?? []) ids.add(id);

  const all = await loadBookItems(book);
  for (const { entry } of all) {
    const loc = (entry.data as { location?: string }).location;
    if (loc === placeId) ids.add(entry.data.id);
  }

  for (const person of occupants) {
    for (const id of crosslinks.occupant_items[person] ?? []) ids.add(id);
  }

  return resolveIds([...ids], index);
}

/** 名物页：同地其他名物 */
export async function relatedItemsAtSameLocation(
  book: string,
  locationId: string | undefined,
  excludeId: string
): Promise<ItemRef[]> {
  if (!locationId || book !== crosslinks.book) return [];
  const all = await relatedItemsForPlace(book, locationId, []);
  return all.filter((r) => r.id !== excludeId);
}

export function itemLocationId(entry: ItemEntry['entry']): string | undefined {
  return (entry.data as { location?: string }).location;
}

export async function relatedItemsForChapter(
  book: string,
  itemIds: string[]
): Promise<ItemRef[]> {
  const index = await itemIndex(book);
  return resolveIds(itemIds, index);
}
