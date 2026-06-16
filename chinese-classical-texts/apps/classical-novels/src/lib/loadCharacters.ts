import { getCollection, type CollectionEntry } from 'astro:content';
import charactersIndex from '../data/characters_index.json';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type CharacterEntry = CollectionEntry<'characters'>;

function fromSnapshot(book: string): CharacterEntry[] {
  const rows = snapshotEntries(charactersIndex as SnapshotIndex<CharacterEntry['data']>, book);
  return rows.map((data) => wrapEntry('characters', `${data.id}.md`, data) as CharacterEntry);
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
