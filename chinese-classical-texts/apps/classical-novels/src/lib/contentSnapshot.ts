/** 书目 slug ↔ 中文名，供 JSON 快照回退共用 */
export const SLUG_BY_BOOK: Record<string, string> = {
  红楼梦: 'honglou',
  金瓶梅: 'jinpingmei',
  西游记: 'xiyouji',
};

export type SnapshotBook<T> = {
  book: string;
  slug: string;
  count: number;
  entries: T[];
};

export type SnapshotIndex<T> = {
  generated_by: string;
  books: Record<string, SnapshotBook<T>>;
};

export function snapshotEntries<T>(
  index: SnapshotIndex<T>,
  book: string,
): T[] {
  const slug = SLUG_BY_BOOK[book];
  if (!slug) return [];
  return index.books[slug]?.entries ?? [];
}

export function wrapEntry<T>(
  collection: string,
  id: string,
  data: T,
): { id: string; collection: string; data: T; body: string } {
  return { id, collection, data, body: '' };
}
