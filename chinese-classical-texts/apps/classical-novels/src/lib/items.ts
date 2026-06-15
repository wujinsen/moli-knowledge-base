import type { CollectionEntry } from 'astro:content';

export type ItemKind = 'medicine' | 'dish' | 'costume' | 'custom' | 'artifact';

export type ItemEntry = {
  kind: ItemKind;
  entry: CollectionEntry<'medicines' | 'dishes' | 'costumes' | 'customs' | 'artifacts'>;
};

const KIND_LABEL: Record<ItemKind, string> = {
  medicine: '医药',
  dish: '饮食',
  costume: '服饰',
  custom: '民俗',
  artifact: '法宝',
};

export function kindLabel(kind: ItemKind): string {
  return KIND_LABEL[kind];
}

export function itemsIndexTitle(book: string): string {
  return book === '西游记' ? '法宝谱系' : '名物百科';
}

const COLLECTION_BY_KIND = {
  artifact: 'artifacts',
  medicine: 'medicines',
  dish: 'dishes',
  costume: 'costumes',
  custom: 'customs',
} as const;

export async function getItemEntry(kind: ItemKind, id: string): Promise<ItemEntry['entry'] | undefined> {
  const { getCollection } = await import('astro:content');
  const collection = COLLECTION_BY_KIND[kind];
  const rows = await getCollection(collection);
  return rows.find((r) => r.data.id === id);
}

export async function loadBookItems(bookName: string): Promise<ItemEntry[]> {
  const { getCollection } = await import('astro:content');
  const [medicines, dishes, costumes, customs, artifacts] = await Promise.all([
    getCollection('medicines'),
    getCollection('dishes'),
    getCollection('costumes'),
    getCollection('customs'),
    getCollection('artifacts'),
  ]);

  const filter = <T extends { book: string }>(rows: { data: T }[]) =>
    rows.filter((r) => r.data.book === bookName);

  return [
    ...filter(artifacts).map((entry) => ({ kind: 'artifact' as const, entry })),
    ...filter(medicines).map((entry) => ({ kind: 'medicine' as const, entry })),
    ...filter(dishes).map((entry) => ({ kind: 'dish' as const, entry })),
    ...filter(costumes).map((entry) => ({ kind: 'costume' as const, entry })),
    ...filter(customs).map((entry) => ({ kind: 'custom' as const, entry })),
  ].sort((a, b) => a.entry.data.name.localeCompare(b.entry.data.name, 'zh-CN'));
}

export function groupByKind(items: ItemEntry[]): Record<ItemKind, ItemEntry[]> {
  return {
    artifact: items.filter((i) => i.kind === 'artifact'),
    medicine: items.filter((i) => i.kind === 'medicine'),
    dish: items.filter((i) => i.kind === 'dish'),
    costume: items.filter((i) => i.kind === 'costume'),
    custom: items.filter((i) => i.kind === 'custom'),
  };
}
