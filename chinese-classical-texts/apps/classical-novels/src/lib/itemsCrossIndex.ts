/** B7/C4 名物纵切：章回 × 人物 × 地点 × 名物交叉索引 */

import itemsCrossIndexJson from '../data/items_cross_index.json';
import type { ItemKind } from './itemsKind';
import { kindLabel } from './itemsKind';

export interface ItemsCrossRow {
  id: string;
  name: string;
  kind: ItemKind;
}

export interface ItemsCrossIndex {
  byChapter: { chapter: number; rows: ItemsCrossRow[] }[];
  byCharacter: { character: string; rows: ItemsCrossRow[] }[];
  byLocation: { location: string; rows: ItemsCrossRow[] }[];
  entries: ItemsCrossRow[];
}

type ItemsIndexBook = {
  book: string;
  slug: string;
  count: number;
  byChapter: Record<string, ItemsCrossRow[]>;
  byCharacter: Record<string, ItemsCrossRow[]>;
  byLocation?: Record<string, ItemsCrossRow[]>;
  entries: ItemsCrossRow[];
};

type ItemsCrossIndexFile = {
  books: Record<string, ItemsIndexBook>;
};

const INDEX = itemsCrossIndexJson as ItemsCrossIndexFile;

function normalizeIndex(raw: ItemsIndexBook): ItemsCrossIndex {
  const byChapter = Object.entries(raw.byChapter)
    .map(([ch, rows]) => ({ chapter: Number(ch), rows }))
    .filter((g) => g.rows.length > 0)
    .sort((a, b) => a.chapter - b.chapter);

  const byCharacter = Object.entries(raw.byCharacter)
    .map(([character, rows]) => ({ character, rows }))
    .filter((g) => g.rows.length > 0)
    .sort((a, b) => b.rows.length - a.rows.length || a.character.localeCompare(b.character, 'zh'));

  const byLocation = Object.entries(raw.byLocation ?? {})
    .map(([location, rows]) => ({ location, rows }))
    .filter((g) => g.rows.length > 0)
    .sort((a, b) => b.rows.length - a.rows.length || a.location.localeCompare(b.location, 'zh'));

  return { byChapter, byCharacter, byLocation, entries: raw.entries };
}

export function getItemsCrossIndex(bookSlug: string): ItemsCrossIndex | null {
  const raw = INDEX.books[bookSlug];
  if (!raw) return null;
  return normalizeIndex(raw);
}

export function relatedItemsForCharacter(bookSlug: string, charId: string): ItemsCrossRow[] {
  const idx = getItemsCrossIndex(bookSlug);
  if (!idx) return [];
  return idx.byCharacter.find((g) => g.character === charId)?.rows ?? [];
}

export function relatedItemsForChapter(bookSlug: string, chapter: number): ItemsCrossRow[] {
  const idx = getItemsCrossIndex(bookSlug);
  if (!idx) return [];
  return idx.byChapter.find((g) => g.chapter === chapter)?.rows ?? [];
}

export function relatedItemsForLocation(bookSlug: string, locationId: string): ItemsCrossRow[] {
  const idx = getItemsCrossIndex(bookSlug);
  if (!idx) return [];
  return idx.byLocation.find((g) => g.location === locationId)?.rows ?? [];
}

export { kindLabel };
