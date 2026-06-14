import type { CollectionEntry } from 'astro:content';

export type ItemKind = 'medicine' | 'dish' | 'costume' | 'custom';

export type ItemEntry = {
  kind: ItemKind;
  entry: CollectionEntry<'medicines' | 'dishes' | 'costumes' | 'customs'>;
};

const KIND_LABEL: Record<ItemKind, string> = {
  medicine: '医药',
  dish: '饮食',
  costume: '服饰',
  custom: '民俗',
};

export function kindLabel(kind: ItemKind): string {
  return KIND_LABEL[kind];
}

export async function loadBookItems(bookName: string): Promise<ItemEntry[]> {
  const { getCollection } = await import('astro:content');
  const [medicines, dishes, costumes, customs] = await Promise.all([
    getCollection('medicines'),
    getCollection('dishes'),
    getCollection('costumes'),
    getCollection('customs'),
  ]);

  const filter = <T extends { book: string }>(rows: { data: T }[]) =>
    rows.filter((r) => r.data.book === bookName);

  return [
    ...filter(medicines).map((entry) => ({ kind: 'medicine' as const, entry })),
    ...filter(dishes).map((entry) => ({ kind: 'dish' as const, entry })),
    ...filter(costumes).map((entry) => ({ kind: 'costume' as const, entry })),
    ...filter(customs).map((entry) => ({ kind: 'custom' as const, entry })),
  ].sort((a, b) => a.entry.data.name.localeCompare(b.entry.data.name, 'zh-CN'));
}

export function groupByKind(items: ItemEntry[]): Record<ItemKind, ItemEntry[]> {
  return {
    medicine: items.filter((i) => i.kind === 'medicine'),
    dish: items.filter((i) => i.kind === 'dish'),
    costume: items.filter((i) => i.kind === 'costume'),
    custom: items.filter((i) => i.kind === 'custom'),
  };
}
