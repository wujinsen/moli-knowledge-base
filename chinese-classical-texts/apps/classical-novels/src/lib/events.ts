/** 事件 / 劫难数据（纯函数，不含 astro:content） */

export interface EventData {
  id: string;
  subtype: string;
  tribulation_no?: number | null;
  financial_kind?: string;
  amount_liang?: number | null;
  transaction_refs?: string[];
  title: string;
  aliases: string[];
  chapters: number[];
  locations: string[];
  characters: string[];
  monsters: string[];
  artifacts: string[];
  prev?: string;
  next?: string;
  tags: string[];
  summary?: string;
}

export type EventEntry = { data: EventData };

export interface TimelinePhase {
  key: string;
  label: string;
  range: [number, number];
}

export const TRIBULATION_PHASES: TimelinePhase[] = [
  { key: 'origin', label: '前世因缘', range: [1, 4] },
  { key: 'start', label: '初出长安', range: [5, 16] },
  { key: 'mid', label: '中途魔障', range: [17, 55] },
  { key: 'late', label: '后期险途', range: [56, 79] },
  { key: 'finish', label: '功果圆满', range: [80, 81] },
];

export function phaseFor(no: number): TimelinePhase {
  return TRIBULATION_PHASES.find((p) => no >= p.range[0] && no <= p.range[1]) ?? TRIBULATION_PHASES[2];
}

export function sortEvents(events: EventEntry[]): EventEntry[] {
  return [...events].sort((a, b) => {
    const na = a.data.tribulation_no ?? 999;
    const nb = b.data.tribulation_no ?? 999;
    return na - nb;
  });
}

/** 金瓶梅 · 发家—攀升—鼎盛—衰败（按首现回目） */
export const JPM_CHAIN_PHASES: TimelinePhase[] = [
  { key: 'rise', label: '发家根基', range: [1, 17] },
  { key: 'climb', label: '政商攀升', range: [18, 40] },
  { key: 'peak', label: '鼎盛极奢', range: [41, 65] },
  { key: 'fall', label: '衰败散府', range: [66, 100] },
];

export function chainPhaseFor(chapter: number): TimelinePhase {
  return (
    JPM_CHAIN_PHASES.find((p) => chapter >= p.range[0] && chapter <= p.range[1]) ??
    JPM_CHAIN_PHASES[2]
  );
}

export function sortChainEvents(events: EventEntry[]): EventEntry[] {
  return [...events].sort((a, b) => {
    const ca = a.data.chapters[0] ?? 999;
    const cb = b.data.chapters[0] ?? 999;
    if (ca !== cb) return ca - cb;
    return a.data.id.localeCompare(b.data.id, 'zh-CN');
  });
}

export function eventSubtypeLabel(subtype: string, financialKind?: string): string {
  if (subtype === 'financial') return financialKind ? `白银·${financialKind}` : '白银';
  if (subtype === 'plot') return '情节';
  return '劫难';
}

export function formatLiangAmount(liang?: number | null): string | undefined {
  if (liang == null) return undefined;
  return `${liang}两`;
}

export function chapterLabel(chapters: number[]): string {
  if (chapters.length === 0) return '—';
  if (chapters.length === 1) return `第${chapters[0]}回`;
  return `第${chapters[0]}–${chapters[chapters.length - 1]}回`;
}

export function displayTitle(d: EventData): string {
  if (d.aliases.length > 0) return `${d.title}（${d.aliases[0]}）`;
  return d.title;
}
