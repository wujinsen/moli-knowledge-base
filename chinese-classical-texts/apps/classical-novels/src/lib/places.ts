import type { CollectionEntry } from 'astro:content';

export type PlaceEntry = CollectionEntry<'locations'>;

const TYPE_LABEL: Record<string, string> = {
  location: '地点',
  building: '建筑',
  garden: '园林',
  temple: '寺庵',
  realm: '幻境',
};

export function typeLabel(type: string): string {
  return TYPE_LABEL[type] ?? type;
}

export async function loadBookPlaces(bookName: string): Promise<PlaceEntry[]> {
  const { getCollection } = await import('astro:content');
  return (await getCollection('locations'))
    .filter((l) => l.data.book === bookName)
    .sort((a, b) => a.data.name.localeCompare(b.data.name, 'zh-CN'));
}

const CATEGORY_ORDER = [
  '花园',
  '府邸',
  '院落',
  '亭',
  '堂',
  '馆',
  '榭',
  '楼',
  '阁',
  '庵',
  '闸',
  '祠',
  '幻境',
  '市街',
  '其他',
] as const;

export function groupByCategory(places: PlaceEntry[]): Map<string, PlaceEntry[]> {
  const map = new Map<string, PlaceEntry[]>();
  for (const p of places) {
    const cat = p.data.category ?? '其他';
    if (!map.has(cat)) map.set(cat, []);
    map.get(cat)!.push(p);
  }
  for (const [, list] of map) {
    list.sort((a, b) => a.data.name.localeCompare(b.data.name, 'zh-CN'));
  }
  return map;
}

export function sortedCategories(map: Map<string, PlaceEntry[]>): string[] {
  const keys = [...map.keys()];
  return keys.sort((a, b) => {
    const ia = CATEGORY_ORDER.indexOf(a as (typeof CATEGORY_ORDER)[number]);
    const ib = CATEGORY_ORDER.indexOf(b as (typeof CATEGORY_ORDER)[number]);
    const ai = ia === -1 ? 999 : ia;
    const bi = ib === -1 ? 999 : ib;
    return ai - bi || a.localeCompare(b, 'zh-CN');
  });
}

export function gardenChildren(places: PlaceEntry[], parentId: string): PlaceEntry[] {
  return places
    .filter((p) => p.data.parent === parentId)
    .sort((a, b) => a.data.name.localeCompare(b.data.name, 'zh-CN'));
}
