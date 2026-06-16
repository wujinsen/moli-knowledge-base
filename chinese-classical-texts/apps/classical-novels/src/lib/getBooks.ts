import { getCollection, type CollectionEntry } from 'astro:content';
import { BOOKS_CATALOG, catalogBookBySlug } from './booksCatalog';

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
 * features 与 BOOKS_CATALOG 取并集，避免陈旧 content store 漏掉 items / kaozheng 等开关导致模块 404 或空白。
 */
export async function getBooks(): Promise<BookEntry[]> {
  try {
    const fromStore = await getCollection('books');
    if (fromStore.length > 0) {
      return fromStore.map((entry) => {
        const cat = catalogBookBySlug(entry.data.slug);
        if (!cat) return entry;
        const storeFeatures = entry.data.features ?? [];
        const merged = [...new Set([...storeFeatures, ...cat.features])];
        const unchanged =
          merged.length === storeFeatures.length && merged.every((f) => storeFeatures.includes(f));
        if (unchanged) return entry;
        return {
          ...entry,
          data: { ...entry.data, features: merged },
        } as BookEntry;
      });
    }
  } catch {
    /* content store unavailable */
  }
  return catalogEntries();
}
