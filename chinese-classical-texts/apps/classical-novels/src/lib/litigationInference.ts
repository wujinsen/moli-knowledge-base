/** 司法诉讼推演（build_litigation_inference.py · inference 层） */

import jpmLitigation from '../data/jinpingmei.litigation-inference.json';

export interface LitigationTier {
  id: string;
  label: string;
  desc: string;
}

export interface LitigationBribery {
  chapter: number;
  amount_liang?: number;
  party: string;
  note?: string;
  tx_ref?: string;
  source?: 'transaction' | 'manual';
  subtype?: string;
}

export interface LitigationCaseLinks {
  saga?: string;
  chain_focus?: string;
  chain_financial?: string;
  chain_focus_note?: string;
  silver_tx?: string[];
  topic?: string;
  silver?: boolean;
}

export interface LitigationCase {
  id: string;
  tier: string;
  title: string;
  chapters: number[];
  anchor_chapter: number;
  parties: Record<string, string[]>;
  locations: string[];
  bribery: LitigationBribery[];
  transaction_refs?: string[];
  outcome: string;
  inference: string;
  evidence: string[];
  links: LitigationCaseLinks;
}

export interface LitigationChapterRow {
  chapter: number;
  corruption_index: number;
  corruption_smooth: number;
  case_ids: string[];
  petition_count: number;
  phase: string;
}

export interface LitigationOfficial {
  id: string;
  role: string;
  cases: string[];
  inference: string;
}

export interface LitigationInsight {
  title: string;
  body: string;
  evidence: string[];
}

export interface LitigationMilestone {
  id: string;
  title: string;
  chapter: number;
  tier: string;
  href: string;
  saga?: string;
  chain_focus?: string;
  chain_href?: string;
}

export interface LitigationInferenceData {
  book: string;
  slug: string;
  generated?: string;
  inference_note: string;
  tiers: LitigationTier[];
  phases: { label: string; from: number; to: number }[];
  cases: LitigationCase[];
  milestones: LitigationMilestone[];
  by_chapter: LitigationChapterRow[];
  officials: LitigationOfficial[];
  social: {
    title: string;
    inference: string;
    insights: LitigationInsight[];
  };
  global_insights: LitigationInsight[];
  stats: {
    case_count: number;
    chapters_with_litigation: number;
    peak_corruption_chapter: number;
    peak_corruption: number;
    bribery_from_transactions?: number;
    transaction_count?: number;
  };
}

const INDEX: Record<string, LitigationInferenceData> = {
  jinpingmei: jpmLitigation as LitigationInferenceData,
};

export function getLitigationInference(bookSlug: string): LitigationInferenceData | null {
  return INDEX[bookSlug] ?? null;
}

export const LITIGATION_DEFAULT_CHAPTER: Record<string, number> = {
  jinpingmei: 48,
};

export const LITIGATION_CHAPTER_JUMP: Record<string, number[]> = {
  jinpingmei: [6, 10, 14, 39, 48, 87, 98],
};

export const LITIGATION_TIER_COLORS: Record<string, string> = {
  county: '#60a5fa',
  cross_region: '#fbbf24',
  capital: '#f472b6',
};

export const LITIGATION_TIER_LABELS: Record<string, string> = {
  county: '基层',
  cross_region: '跨区',
  capital: '国家级',
};

export function litigationCaseForChainFocus(
  data: LitigationInferenceData | null,
  chainFocus: string,
): LitigationCase | undefined {
  if (!data) return undefined;
  return data.cases.find((c) => c.links.chain_focus === chainFocus || c.links.chain_financial === chainFocus);
}

export function litigationChapterHref(bookSlug: string, chapter: number): string {
  return `/${bookSlug}/litigation?chapter=${chapter}`;
}

export function litigationChartPalette(bookSlug: string) {
  void bookSlug;
  return {
    corruption: '#c084fc',
    corruptionArea: '#c084fc22',
    milestone: '#9c8450',
    milestoneDim: '#5c6359',
  };
}
