/** D1–D2：西游记八十一难索引 + 靠山统计（build_nan.py 生成） */

import nanJson from '../data/xiyouji.nan.json';

export type NanCamp = '佛门' | '道门' | '天庭' | '打杀自死' | '未知';

export interface NanMonster {
  name: string;
  原型: string;
  收服者: string;
  camp: NanCamp;
  法宝: string[];
}

export interface NanRow {
  no: number;
  id: string;
  title: string;
  aliases: string[];
  chapters: number[];
  phase: string;
  phaseLabel: string;
  summary: string;
  monsters: NanMonster[];
  locations: string[];
  artifacts: string[];
}

export interface NanPhase {
  key: string;
  label: string;
  range: [number, number];
  count: number;
}

export interface NanData {
  book: string;
  slug: string;
  total: number;
  phases: NanPhase[];
  tribulations: NanRow[];
  stats: {
    by_camp: Record<string, number>;
    top_monsters: [string, number][];
    top_artifacts: [string, number][];
    top_locations: [string, number][];
  };
}

const NAN = nanJson as unknown as NanData;

export const NAN_CAMPS: NanCamp[] = ['佛门', '道门', '天庭', '打杀自死', '未知'];

/** 阵营色：有靠山（暖金/青/赤）vs 无背景打杀（玄）vs 未知（灰） */
export const CAMP_COLOR: Record<string, string> = {
  佛门: '#c08a2b',
  道门: '#3f7d4f',
  天庭: '#5a6fa8',
  打杀自死: '#9a3b2e',
  未知: '#8a8a8a',
};

export const CAMP_DESC: Record<string, string> = {
  佛门: '佛门坐骑/部属，被佛菩萨收回',
  道门: '道门坐骑/童子，被老君等收回',
  天庭: '天庭星宿/部将下界，被天将收押',
  打杀自死: '无背景野妖，被师徒打杀或自灭',
  未知: '收服者待考',
};

export function getNan(bookSlug: string): NanData | null {
  return bookSlug === 'xiyouji' ? NAN : null;
}
