import type { CollectionEntry } from 'astro:content';
import itemsIndex from '../data/items_index.json';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type ItemKind = 'medicine' | 'dish' | 'costume' | 'custom' | 'artifact';

type ItemData = CollectionEntry<'medicines' | 'dishes' | 'costumes' | 'customs' | 'artifacts'>['data'];

type ItemSnapshotRow = ItemData & { kind: ItemKind };

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

function fromSnapshot(bookName: string): ItemEntry[] {
  const rows = snapshotEntries(itemsIndex as SnapshotIndex<ItemSnapshotRow>, bookName);
  return rows.map(({ kind, ...data }) => {
    const collection = COLLECTION_BY_KIND[kind];
    const entry = wrapEntry(collection, `${data.id}.md`, data) as ItemEntry['entry'];
    return { kind, entry };
  });
}

export async function getItemEntry(kind: ItemKind, id: string): Promise<ItemEntry['entry'] | undefined> {
  const { getCollection } = await import('astro:content');
  const collection = COLLECTION_BY_KIND[kind];
  try {
    const rows = await getCollection(collection);
    if (rows.length > 0) {
      return rows.find((r) => r.data.id === id);
    }
  } catch {
    /* content store unavailable */
  }
  const bookRows = Object.values((itemsIndex as SnapshotIndex<ItemSnapshotRow>).books).flatMap((b) => b.entries);
  const hit = bookRows.find((r) => r.kind === kind && r.id === id);
  if (!hit) return undefined;
  const { kind: k, ...data } = hit;
  return wrapEntry(collection, `${data.id}.md`, data) as ItemEntry['entry'];
}

export async function loadBookItems(bookName: string): Promise<ItemEntry[]> {
  const { getCollection } = await import('astro:content');
  try {
    const [medicines, dishes, costumes, customs, artifacts] = await Promise.all([
      getCollection('medicines'),
      getCollection('dishes'),
      getCollection('costumes'),
      getCollection('customs'),
      getCollection('artifacts'),
    ]);
    if (medicines.length + dishes.length + costumes.length + customs.length + artifacts.length > 0) {
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
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(bookName).sort((a, b) =>
    a.entry.data.name.localeCompare(b.entry.data.name, 'zh-CN'),
  );
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
