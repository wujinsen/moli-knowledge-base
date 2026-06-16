import { getCollection, type CollectionEntry } from 'astro:content';
import eventsIndex from '../data/events_index.json';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type EventEntry = CollectionEntry<'events'>;

function fromSnapshot(book?: string): EventEntry[] {
  const rows = book
    ? snapshotEntries(eventsIndex as SnapshotIndex<EventEntry['data']>, book)
    : Object.values((eventsIndex as SnapshotIndex<EventEntry['data']>).books).flatMap((b) => b.entries);
  return rows.map((data) => {
    const id = `${data.id}.md`;
    return wrapEntry('events', id, data) as EventEntry;
  });
}

/** 全书或单书事件；content store 为空时回退 events_index.json */
export async function loadEvents(book?: string): Promise<EventEntry[]> {
  try {
    const fromStore = await getCollection('events');
    if (fromStore.length > 0) {
      return book ? fromStore.filter((e) => e.data.book === book) : fromStore;
    }
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(book);
}
