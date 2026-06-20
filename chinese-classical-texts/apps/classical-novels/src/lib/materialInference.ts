/** 医药 / 服饰 / 民俗 物质推演（build_material_inference.py） */

import hlmMed from '../data/honglou.medicine-inference.json';
import jpmMed from '../data/jinpingmei.medicine-inference.json';
import hlmCostume from '../data/honglou.costume-inference.json';
import jpmCostume from '../data/jinpingmei.costume-inference.json';
import hlmCustom from '../data/honglou.custom-inference.json';
import jpmCustom from '../data/jinpingmei.custom-inference.json';

export type MaterialDomain = 'medicine' | 'costume' | 'custom';

export interface InferenceAxisMeta {
  id: string;
  label: string;
  desc: string;
}

export interface InferenceChapterRow {
  chapter: number;
  entity_count: number;
  luxury: number;
  balance: number;
  luxury_smooth: number;
  balance_smooth: number;
  axes: Record<string, number>;
  phase: string;
  entities: string[];
}

export interface InferenceCharacterRow {
  id: string;
  name: string;
  social_tier?: string;
  entity_count: number;
  axes: Record<string, number>;
  balance_score: number;
  risk_tags: string[];
  inference: string;
  sample_entities: string[];
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
  insights: { title: string; body: string; evidence: string[] }[];
}

export interface InferenceInsight {
  title: string;
  body: string;
  evidence: string[];
}

export interface MaterialInferenceData {
  domain: MaterialDomain;
  book: string;
  slug: string;
  inference_note: string;
  curve_labels: { primary: string; secondary: string };
  axes: InferenceAxisMeta[];
  phases: { label: string; from: number; to: number }[];
  saga_milestones?: {
    id: string;
    title: string;
    chapters: number[];
    chapter: number;
    href: string;
  }[];
  by_chapter: InferenceChapterRow[];
  characters: InferenceCharacterRow[];
  social: SocialBlock;
  global_insights: InferenceInsight[];
  stats: {
    entity_count: number;
    occurrence_rows: number;
    chapters_with_data: number;
    peak_chapter: number;
    peak_primary: number;
    saga_milestones?: number;
    social_segments: number;
  };
}

const INDEX: Record<MaterialDomain, Record<string, MaterialInferenceData>> = {
  medicine: {
    honglou: hlmMed as MaterialInferenceData,
    jinpingmei: jpmMed as MaterialInferenceData,
  },
  costume: {
    honglou: hlmCostume as MaterialInferenceData,
    jinpingmei: jpmCostume as MaterialInferenceData,
  },
  custom: {
    honglou: hlmCustom as MaterialInferenceData,
    jinpingmei: jpmCustom as MaterialInferenceData,
  },
};

export function getMaterialInference(
  bookSlug: string,
  domain: MaterialDomain,
): MaterialInferenceData | null {
  return INDEX[domain]?.[bookSlug] ?? null;
}

export const DOMAIN_UI: Record<
  MaterialDomain,
  { glyph: string; title: string; curveTitle: string; charTitle: string; entityLabel: string }
> = {
  medicine: {
    glyph: '医',
    title: '药疗推演',
    curveTitle: '全书药疗水平',
    charTitle: '人物药疗推演',
    entityLabel: '条医药实体',
  },
  costume: {
    glyph: '衣',
    title: '服饰推演',
    curveTitle: '全书服饰精神面貌',
    charTitle: '人物服饰推演',
    entityLabel: '条服饰实体',
  },
  custom: {
    glyph: '俗',
    title: '民俗推演',
    curveTitle: '全书民俗状态',
    charTitle: '人物礼俗参与',
    entityLabel: '条民俗实体',
  },
};

export const MATERIAL_AXIS_COLORS: Record<MaterialDomain, Record<string, string>> = {
  medicine: {
    pulse_refined: '#818cf8',
    tonic_luxury: '#c084fc',
    prescription_norm: '#60a5fa',
    folk_belief: '#fbbf24',
    quack_risk: '#f87171',
    acute_crisis: '#fb923c',
  },
  costume: {
    silk_brocade: '#f472b6',
    jewelry_rank: '#fbbf24',
    ceremonial: '#c084fc',
    daily_plain: '#4ade80',
    symbolic_token: '#60a5fa',
    foreign_rare: '#fb923c',
  },
  custom: {
    festival: '#fbbf24',
    funeral_rite: '#94a3b8',
    marriage: '#f472b6',
    clan_institution: '#818cf8',
    folk_magic: '#fb923c',
    state_norm: '#f87171',
  },
};

export const MATERIAL_DEFAULT_CHAPTER: Record<string, Partial<Record<MaterialDomain, number>>> = {
  honglou: { medicine: 10, costume: 18, custom: 53 },
  jinpingmei: { medicine: 49, costume: 27, custom: 49 },
};

export const MATERIAL_CHAPTER_JUMP: Record<string, Partial<Record<MaterialDomain, number[]>>> = {
  honglou: {
    medicine: [1, 10, 27, 52, 71, 97, 120],
    costume: [1, 18, 38, 53, 71, 120],
    custom: [1, 18, 53, 64, 75, 120],
  },
  jinpingmei: {
    medicine: [1, 27, 49, 79, 100],
    costume: [1, 27, 49, 79, 100],
    custom: [1, 27, 49, 79, 100],
  },
};

export const TIER_LABELS: Record<string, string> = {
  elite: '权贵/主子',
  middling: '中层',
  folk: '市井/民间',
  general: '制度性',
};
