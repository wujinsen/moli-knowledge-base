/** 事件 / 劫难数据（纯函数，不含 astro:content） */

export interface EventData {
  id: string;
  subtype: string;
  tribulation_no?: number | null;
  edition?: string;
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
  variants?: { edition: string; claim: string; source?: string }[];
  contradicts?: string[];
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

/** 红楼梦 · 大事记五期（按回目；后 40 回属程高本续补） */
export const HLM_SAGA_PHASES: TimelinePhase[] = [
  { key: 'prologue', label: '序幕·缘起', range: [1, 15] },
  { key: 'zenith', label: '烈火烹油·盛极', range: [16, 22] },
  { key: 'awaken', label: '春情觉醒', range: [23, 73] },
  { key: 'collapse', label: '自杀自灭·崩塌', range: [74, 80] },
  { key: 'ruin', label: '白茫茫·覆灭', range: [81, 120] },
];

/** 后 40 回（程高本续补）起始回 */
export const HLM_CHENGGAO_FROM = 81;

/** 金瓶梅 · 大事记五期（暴发—鼎盛—衰败） */
export const JPM_SAGA_PHASES: TimelinePhase[] = [
  { key: 'sin', label: '罪恶开端', range: [1, 13] },
  { key: 'wealth', label: '人财暴涨', range: [14, 29] },
  { key: 'zenith', label: '烈火烹油·巅峰', range: [30, 58] },
  { key: 'turn', label: '由盛转衰', range: [59, 79] },
  { key: 'scatter', label: '树倒猢狲散', range: [80, 100] },
];

/** 西游记 · 大事记五期（叛逆—收心—修成） */
export const XY_SAGA_PHASES: TimelinePhase[] = [
  { key: 'rebel', label: '心猿出世·叛逆', range: [1, 13] },
  { key: 'start', label: '收心启程', range: [14, 26] },
  { key: 'trial', label: '历劫考验', range: [27, 58] },
  { key: 'temper', label: '灭欲修心', range: [59, 97] },
  { key: 'attain', label: '功成证真', range: [98, 100] },
];

export function sagaPhasesForBook(book: string): TimelinePhase[] {
  if (book === '金瓶梅') return JPM_SAGA_PHASES;
  if (book === '西游记') return XY_SAGA_PHASES;
  return HLM_SAGA_PHASES;
}

export function sagaPhaseForBook(book: string, chapter: number): TimelinePhase {
  const phases = sagaPhasesForBook(book);
  return phases.find((p) => chapter >= p.range[0] && chapter <= p.range[1]) ?? phases[0];
}

/** 红楼梦专用：按回判断分期（保留向后兼容） */
export function sagaPhaseFor(chapter: number): TimelinePhase {
  return sagaPhaseForBook('红楼梦', chapter);
}

/** 事件所属版本：显式 edition 优先，否则按回目推断（>80 回为程高本补） */
export function eventEdition(d: EventData): string {
  if (d.edition) return d.edition;
  const ch = d.chapters[0] ?? 0;
  return ch >= HLM_CHENGGAO_FROM ? '程高本' : '脂砚斋本';
}

export function isChenggaoEvent(d: EventData): boolean {
  return eventEdition(d) === '程高本';
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
