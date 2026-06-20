import { getCollection, type CollectionEntry } from 'astro:content';
import charactersIndex from '../data/characters_index.json';
import { getBooks } from './getBooks';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type CharacterEntry = CollectionEntry<'characters'>;

export type CharacterPageProps = {
  entry: CharacterEntry;
  slug: string;
  features: string[];
};

const storeKey = (book: string, id: string) => `${book}\0${id}`;

function fromSnapshot(book: string): CharacterEntry[] {
  const rows = snapshotEntries(charactersIndex as SnapshotIndex<CharacterEntry['data']>, book);
  return rows.map((data) => wrapEntry('characters', `${data.id}.md`, data) as CharacterEntry);
}

async function characterStoreByKey(): Promise<Map<string, CharacterEntry>> {
  try {
    const fromStore = await getCollection('characters');
    if (fromStore.length > 0) {
      return new Map(fromStore.map((c) => [storeKey(c.data.book, c.data.id), c]));
    }
  } catch {
    /* content store unavailable */
  }
  return new Map();
}

/** 列出某书全部人物；content store 为空时回退 characters_index.json */
export async function loadCharacters(book: string): Promise<CharacterEntry[]> {
  try {
    const fromStore = await getCollection('characters');
    if (fromStore.length > 0) {
      return fromStore
        .filter((c) => c.data.book === book)
        .sort((a, b) => (b.data.weight ?? 0) - (a.data.weight ?? 0));
    }
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(book);
}

/** 快照条目无正文，不可 render() */
export function isSnapshotCharacterEntry(entry: CharacterEntry): boolean {
  return !entry.body?.trim();
}

/**
 * 人物页 getStaticPaths：与图鉴 loadCharacters 同源。
 * dev 下 content store 尚未 sync 时仍从 characters_index.json 生成路由，避免图鉴可点而 /c/ 404。
 */
export async function characterPageStaticPaths(): Promise<
  { params: { book: string; id: string }; props: CharacterPageProps }[]
> {
  const books = await getBooks();
  const store = await characterStoreByKey();
  const paths: { params: { book: string; id: string }; props: CharacterPageProps }[] = [];

  for (const b of books) {
    const entries = await loadCharacters(b.data.book);
    for (const entry of entries) {
      const key = storeKey(entry.data.book, entry.data.id);
      paths.push({
        params: { book: b.data.slug, id: entry.data.id },
        props: {
          entry: store.get(key) ?? entry,
          slug: b.data.slug,
          features: b.data.features,
        },
      });
    }
  }
  return paths;
}
