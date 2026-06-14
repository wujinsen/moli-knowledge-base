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

/** 书目主场景根节点（places 页顶栏分组用） */
export const BOOK_PLACE_ROOT: Partial<
  Record<string, { id: string; title: string; pageTitle: string; blurb: string }>
> = {
  红楼梦: {
    id: '大观园',
    title: '大观园',
    pageTitle: '大观园 · 建筑居所',
    blurb: '府邸、园林、亭榭堂馆',
  },
  金瓶梅: {
    id: '西门府',
    title: '西门府',
    pageTitle: '西门府 · 建筑居所',
    blurb: '府内院落、县城市井、寺观院馆',
  },
};

export function placeRootFor(bookName: string) {
  return BOOK_PLACE_ROOT[bookName];
}
