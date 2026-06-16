import { getCollection, type CollectionEntry } from 'astro:content';
import locationsIndex from '../data/locations_index.json';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type LocationEntry = CollectionEntry<'locations'>;

function fromSnapshot(book: string): LocationEntry[] {
  const rows = snapshotEntries(locationsIndex as SnapshotIndex<LocationEntry['data']>, book);
  return rows.map((data) => {
    const id = `${data.id}.md`;
    return wrapEntry('locations', id, data) as LocationEntry;
  });
}

/** 某书全部地点；content store 为空时回退 locations_index.json */
export async function loadLocations(book: string): Promise<LocationEntry[]> {
  try {
    const fromStore = await getCollection('locations');
    if (fromStore.length > 0) {
      return fromStore.filter((l) => l.data.book === book);
    }
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(book);
}
