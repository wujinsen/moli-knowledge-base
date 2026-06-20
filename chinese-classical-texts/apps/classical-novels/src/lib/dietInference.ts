/** 膳食推演（build_diet_inference.py · inference 层） */

import hlmDiet from '../data/honglou.diet-inference.json';
import jpmDiet from '../data/jinpingmei.diet-inference.json';

export interface DietAxisMeta {
  id: string;
  label: string;
  desc: string;
}

export interface DietChapterRow {
  chapter: number;
  dish_count: number;
  luxury: number;
  balance: number;
  luxury_smooth: number;
  balance_smooth: number;
  axes: Record<string, number>;
  phase: string;
  dishes: string[];
  sources?: string[];
}

export interface DietCharacterRow {
  id: string;
  name: string;
  dish_count: number;
  axes: Record<string, number>;
  balance_score: number;
  risk_tags: string[];
  inference: string;
  medicine_echo: string[];
  sample_dishes: string[];
}

export interface DietSagaMilestone {
  id: string;
  title: string;
  chapters: number[];
  chapter: number;
  href: string;
}

export interface DietInsight {
  title: string;
  body: string;
  evidence: string[];
  axis_ratio?: { heavy: number; light: number };
}

export interface SocialSegment {
  id: string;
  label: string;
  entity_count: number;
  occurrence_weight: number;
  axes: Record<string, number>;
  sample_entities: string[];
}

export interface SocialBlock {
  title: string;
  segments: SocialSegment[];
  global_axes: Record<string, number>;
  inference: string;
  insights: DietInsight[];
}

export interface DietInferenceData {
  book: string;
  slug: string;
  inference_note: string;
  axes: DietAxisMeta[];
  phases: { label: string; from: number; to: number }[];
  saga_milestones?: DietSagaMilestone[];
  by_chapter: DietChapterRow[];
  characters: DietCharacterRow[];
  social?: SocialBlock;
  global_insights: DietInsight[];
  stats: {
    dish_entities: number;
    occurrence_rows?: number;
    manual_axis_entities?: number;
    chapter_item_refs?: number;
    chapters_with_food: number;
    peak_luxury_chapter: number;
    peak_luxury: number;
    saga_milestones?: number;
    social_segments?: number;
  };
}

const INDEX: Record<string, DietInferenceData> = {
  honglou: hlmDiet as DietInferenceData,
  jinpingmei: jpmDiet as DietInferenceData,
};

export function getDietInference(bookSlug: string): DietInferenceData | null {
  return INDEX[bookSlug] ?? null;
}

export const DIET_AXIS_COLORS: Record<string, string> = {
  fine_tonic: '#c084fc',
  fat_sweet: '#fb923c',
  refined_grain: '#fbbf24',
  coarse_balance: '#4ade80',
  feast_luxury: '#f472b6',
  alcohol: '#60a5fa',
};

/** 各书默认聚焦回目（曲线初始 tooltip） */
export const DIET_DEFAULT_CHAPTER: Record<string, number> = {
  honglou: 38,
  jinpingmei: 49,
};

/** 快捷跳转回目 */
export const DIET_CHAPTER_JUMP: Record<string, number[]> = {
  honglou: [1, 18, 38, 41, 60, 71, 84, 97, 120],
  jinpingmei: [1, 20, 49, 59, 79, 89, 100],
};

export const TIER_LABELS: Record<string, string> = {
  elite: '权贵/主子',
  middling: '中层',
  folk: '市井/民间',
  general: '制度性',
};
