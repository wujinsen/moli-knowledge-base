/** 诗词意象 P2：章回 × 人物 × 诗词 交叉索引 */

import type { ImageryEntry } from './loadImagery';
import type { ImageryGraphEdge } from './imagery';
import { subtypeLabel } from './imagery';
import shiIndexJson from '../data/shi_index.json';

export interface ShiCrossRow {
  id: string;
  title: string;
  subtype: string;
  chapters: number[];
  characters: string[];
  hasInference: boolean;
}

export interface ShiCrossIndex {
  byChapter: { chapter: number; rows: ShiCrossRow[] }[];
  byCharacter: { character: string; rows: ShiCrossRow[] }[];
  entries: ShiCrossRow[];
}

export type ImageryRef = Pick<ShiCrossRow, 'id' | 'title' | 'subtype' | 'characters' | 'hasInference'> & {
  chapters?: number[];
};

type ShiIndexBook = {
  book: string;
  slug: string;
  byChapter: Record<string, ShiCrossRow[]>;
  byCharacter: Record<string, ShiCrossRow[]>;
  entries: ShiCrossRow[];
};

type ShiIndexFile = {
  books: Record<string, ShiIndexBook>;
};

const INDEX = shiIndexJson as ShiIndexFile;

const SLUG_BY_BOOK: Record<string, string> = {
  红楼梦: 'honglou',
  金瓶梅: 'jinpingmei',
  西游记: 'xiyouji',
};

function isImageryId(id: string): boolean {
  return id.startsWith('hl-') || id.startsWith('jpm-') || id.startsWith('xyj-');
}

function slugForBook(book: string): string | undefined {
  return SLUG_BY_BOOK[book];
}

function normalizeIndex(raw: ShiIndexBook): ShiCrossIndex {
  const byChapter = Object.entries(raw.byChapter)
    .map(([ch, rows]) => ({ chapter: Number(ch), rows }))
    .filter((g) => g.rows.length > 0)
    .sort((a, b) => a.chapter - b.chapter);

  const byCharacter = Object.entries(raw.byCharacter)
    .map(([character, rows]) => ({ character, rows }))
    .filter((g) => g.rows.length > 0)
    .sort((a, b) => b.rows.length - a.rows.length || a.character.localeCompare(b.character, 'zh'));

  return { byChapter, byCharacter, entries: raw.entries };
}

/** 读取预构建交叉索引（build_shi_index.py） */
export function getShiCrossIndex(bookSlug: string): ShiCrossIndex | null {
  const raw = INDEX.books[bookSlug];
  if (!raw) return null;
  return normalizeIndex(raw);
}

export function getShiCrossIndexByBookName(book: string): ShiCrossIndex | null {
  const slug = slugForBook(book);
  return slug ? getShiCrossIndex(slug) : null;
}

/** 运行时从 imagery 实体构建（dev / 脚本校验用） */
export function buildShiCrossIndex(
  items: ImageryEntry[],
  extraLinks: ImageryGraphEdge[] = [],
): ShiCrossIndex {
  const extraBySource = new Map<string, ImageryGraphEdge[]>();
  for (const e of extraLinks) {
    const list = extraBySource.get(e.source) ?? [];
    list.push(e);
    extraBySource.set(e.source, list);
  }

  const entries: ShiCrossRow[] = items.map((item) => {
    const d = item.data;
    const extra = extraBySource.get(d.id) ?? [];

    const characters = new Set<string>(d.characters);
    for (const l of d.links) {
      if (l.target_kind === 'character' || !isImageryId(l.target)) characters.add(l.target);
    }
    for (const e of extra) {
      if (!isImageryId(e.target)) characters.add(e.target);
    }

    const chapters = new Set<number>(d.chapters);
    for (const l of d.links) {
      if (l.chapter != null) chapters.add(l.chapter);
    }
    for (const e of extra) {
      if (e.chapter != null) chapters.add(e.chapter);
    }

    const hasInference =
      d.links.some((l) => l.inference) || extra.some((e) => e.inference);

    return {
      id: d.id,
      title: d.title,
      subtype: d.subtype,
      chapters: [...chapters].sort((a, b) => a - b),
      characters: [...characters].sort((a, b) => a.localeCompare(b, 'zh')),
      hasInference,
    };
  });

  const byChapterMap = new Map<number, ShiCrossRow[]>();
  const byCharacterMap = new Map<string, ShiCrossRow[]>();

  for (const row of entries) {
    for (const ch of row.chapters) {
      const list = byChapterMap.get(ch) ?? [];
      list.push(row);
      byChapterMap.set(ch, list);
    }
    for (const c of row.characters) {
      const list = byCharacterMap.get(c) ?? [];
      list.push(row);
      byCharacterMap.set(c, list);
    }
  }

  const byChapter = [...byChapterMap.entries()]
    .map(([chapter, rows]) => ({
      chapter,
      rows: [...rows].sort((a, b) => a.title.localeCompare(b.title, 'zh')),
    }))
    .sort((a, b) => a.chapter - b.chapter);

  const byCharacter = [...byCharacterMap.entries()]
    .map(([character, rows]) => ({
      character,
      rows: [...rows].sort((a, b) => a.chapters[0] - b.chapters[0] || a.title.localeCompare(b.title, 'zh')),
    }))
    .sort((a, b) => b.rows.length - a.rows.length || a.character.localeCompare(b.character, 'zh'));

  return { byChapter, byCharacter, entries };
}

export function relatedImageryForCharacter(bookSlug: string, charId: string): ImageryRef[] {
  const idx = getShiCrossIndex(bookSlug);
  if (!idx) return [];
  const group = idx.byCharacter.find((g) => g.character === charId);
  return (group?.rows ?? []).map(({ id, title, subtype, characters, hasInference, chapters }) => ({
    id,
    title,
    subtype,
    characters,
    hasInference,
    chapters,
  }));
}

export function relatedImageryForChapter(bookSlug: string, chapter: number): ImageryRef[] {
  const idx = getShiCrossIndex(bookSlug);
  if (!idx) return [];
  const group = idx.byChapter.find((g) => g.chapter === chapter);
  return (group?.rows ?? []).map(({ id, title, subtype, characters, hasInference, chapters }) => ({
    id,
    title,
    subtype,
    characters,
    hasInference,
    chapters,
  }));
}

export { subtypeLabel };
