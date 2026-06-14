import { getCollection, type CollectionEntry } from 'astro:content';
import { BOOKS_CATALOG } from './booksCatalog';

export type BookEntry = CollectionEntry<'books'>;

function catalogEntries(): BookEntry[] {
  return BOOKS_CATALOG.map((data) => ({
    id: `${data.slug}.md`,
    collection: 'books',
    data,
    body: '',
  })) as BookEntry[];
}

/**
 * 读取书目列表。优先 Astro content store；若 dev 下 data-store 写入失败导致空集合，回退静态 catalog。
 */
export async function getBooks(): Promise<BookEntry[]> {
  try {
    const fromStore = await getCollection('books');
    if (fromStore.length > 0) return fromStore;
  } catch {
    /* content store unavailable */
  }
  return catalogEntries();
}
