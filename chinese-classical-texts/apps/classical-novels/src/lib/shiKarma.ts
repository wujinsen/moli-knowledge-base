/** C6 P3：金瓶梅因果闭环五阶段索引（build_shi_karma.py） */

import karmaJson from '../data/jinpingmei.shi-karma.json';

export type KarmaPhase = '欲起' | '聚敛' | '极盛' | '反噬' | '散尽';

export interface KarmaPhaseItem {
  id: string;
  title: string;
  subtype: string;
  temperature?: '冷' | '热';
  chapter?: number;
  predicate?: string;
  target?: string;
}

export interface KarmaChain {
  id: string;
  name: string;
  summary?: string;
  path: string[];
}

export interface ShiKarmaData {
  book: string;
  slug: string;
  phases: KarmaPhase[];
  by_phase: Record<KarmaPhase, KarmaPhaseItem[]>;
  counts: Record<KarmaPhase, number>;
  chains: KarmaChain[];
}

const KARMA = karmaJson as ShiKarmaData;

export function getShiKarma(bookSlug: string): ShiKarmaData | null {
  return bookSlug === 'jinpingmei' ? KARMA : null;
}

export const KARMA_PHASES: KarmaPhase[] = ['欲起', '聚敛', '极盛', '反噬', '散尽'];
