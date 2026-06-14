/** 关系类型 → 边颜色（深色背景下高对比） */
export const RELATION_COLORS: Record<string, string> = {
  夫妻: '#f472b6',
  父子: '#38bdf8',
  母子: '#7dd3fc',
  兄弟: '#34d399',
  姐妹: '#a78bfa',
  祖孙: '#2dd4bf',
  妯娌: '#c084fc',
  主仆: '#94a3b8',
  师徒: '#fbbf24',
  师兄弟: '#fcd34d',
  同僚: '#60a5fa',
  朋友: '#4ade80',
  结拜: '#fb923c',
  君臣: '#e879f9',
  情人: '#fb7185',
  恋慕: '#fda4af',
  仇敌: '#ef4444',
  敌对: '#f87171',
};

export const FACTION_PALETTE = [
  '#f59e0b',
  '#38bdf8',
  '#a78bfa',
  '#34d399',
  '#fb7185',
  '#94a3b8',
  '#e879f9',
  '#2dd4bf',
];

export function relationColor(type: string): string {
  return RELATION_COLORS[type] ?? '#64748b';
}

export function factionColor(index: number): string {
  return FACTION_PALETTE[index % FACTION_PALETTE.length];
}

/** 每部作品的图谱暗色舞台配色 */
export interface GraphTheme {
  base: string; // 纯色暗底（用于布局 body / 空状态）
  backdrop: string; // 多层渐变舞台背景
  accent: string; // 主强调色（描金 / 铜）
  accentSoft: string; // 高亮文字色
  accentLine: string; // 半透明描边
}

export const GRAPH_THEME: Record<string, GraphTheme> = {
  honglou: {
    base: '#0c0709',
    backdrop:
      'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(159,43,53,0.26) 0%, transparent 55%), radial-gradient(ellipse 60% 55% at 100% 100%, rgba(53,87,102,0.18) 0%, transparent 50%), linear-gradient(180deg, #1b0e12 0%, #0a0608 100%)',
    accent: '#e0b059',
    accentSoft: '#f4d796',
    accentLine: 'rgba(224,176,89,0.4)',
  },
  xiyouji: {
    base: '#0b0a06',
    backdrop:
      'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(192,64,31,0.26) 0%, transparent 55%), radial-gradient(ellipse 60% 55% at 100% 100%, rgba(38,108,124,0.20) 0%, transparent 50%), linear-gradient(180deg, #15110a 0%, #090804 100%)',
    accent: '#e7b53a',
    accentSoft: '#f6df9a',
    accentLine: 'rgba(231,181,58,0.4)',
  },
  jinpingmei: {
    base: '#080b08',
    backdrop:
      'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(58,81,69,0.32) 0%, transparent 55%), radial-gradient(ellipse 60% 55% at 100% 100%, rgba(138,101,50,0.16) 0%, transparent 50%), linear-gradient(180deg, #0f150f 0%, #070908 100%)',
    accent: '#c7ac72',
    accentSoft: '#e3d2a4',
    accentLine: 'rgba(199,172,114,0.4)',
  },
};

export function graphTheme(slug?: string): GraphTheme {
  return GRAPH_THEME[slug ?? ''] ?? GRAPH_THEME.honglou;
}
