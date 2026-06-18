/** C5 版本对勘 J3：异文索引（build_compare.py 生成） */

import jpmCompare from '../data/jinpingmei.compare.json';
import xyjCompare from '../data/xiyouji.compare.json';
import { compareChapterPath } from './editions';

export interface CompareVariantRow {
  id: string;
  category: string;
  summary: string;
  edition_a: string;
  edition_b: string;
  text_a?: string;
  text_b?: string;
  topic_id?: string;
  tags: string[];
  pairs: string[];
}

export interface ComparePairMeta {
  left: string;
  right: string;
  label: string;
  variant_count: number;
  chapters_with_variants: number[];
}

export interface CompareTopicRow {
  id: string;
  chapter: number;
  summary: string;
  variant_ids: string[];
  characters: string[];
}

export interface CompareIndexData {
  book: string;
  slug: string;
  variant_total: number;
  chapter_count_with_variants: number;
  pairs: Record<string, ComparePairMeta>;
  by_chapter: Record<string, CompareVariantRow[]>;
  topics: CompareTopicRow[];
}

const INDEX: Record<string, CompareIndexData> = {
  jinpingmei: jpmCompare as CompareIndexData,
  xiyouji: xyjCompare as CompareIndexData,
};

export function getCompareIndex(bookSlug: string): CompareIndexData | null {
  return INDEX[bookSlug] ?? null;
}

export function variantsForPairChapter(
  index: CompareIndexData,
  pairSlug: string,
  chapter: number,
): CompareVariantRow[] {
  const rows = index.by_chapter[String(chapter)] ?? [];
  return rows.filter((v) => v.pairs.includes(pairSlug));
}

export function compareVariantHref(
  bookSlug: string,
  pairSlug: string,
  chapter: number,
  variantId?: string,
): string {
  const base = compareChapterPath(bookSlug, pairSlug, chapter);
  if (!variantId) return base;
  return `${base}?variant=${encodeURIComponent(variantId)}`;
}

export { compareChapterPath };
