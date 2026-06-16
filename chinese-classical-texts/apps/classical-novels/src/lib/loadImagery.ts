import { getCollection, type CollectionEntry } from 'astro:content';
import imageryIndex from '../data/imagery_index.json';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type ImageryEntry = CollectionEntry<'imagery'>;

function fromSnapshot(book: string): ImageryEntry[] {
  const rows = snapshotEntries(imageryIndex as SnapshotIndex<ImageryEntry['data'] & { _entry_id?: string }>, book);
  return rows.map((data) => {
    const { _entry_id, ...rest } = data;
    const id = _entry_id ? `${_entry_id}.md` : `${rest.id}.md`;
    return wrapEntry('imagery', id, rest as ImageryEntry['data']) as ImageryEntry;
  });
}

/** 某书全部意象条目；content store 为空时回退 imagery_index.json */
export async function loadImagery(book: string): Promise<ImageryEntry[]> {
  try {
    const fromStore = await getCollection('imagery');
    if (fromStore.length > 0) {
      return fromStore.filter((i) => i.data.book === book);
    }
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(book);
}
