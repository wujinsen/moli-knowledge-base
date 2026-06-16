import type { CollectionEntry } from 'astro:content';
import { loadEvents } from './loadEvents';

export type EventEntry = CollectionEntry<'events'>;

/** 大事记 milestone 事件 */
export async function loadSagaEvents(book: string): Promise<EventEntry[]> {
  const all = await loadEvents(book);
  return all.filter((e) => e.data.subtype === 'milestone');
}
