/** 图鉴分组 · 三书共用 catalog 模式 */

import hlmCatalog from '../data/hongloumeng.bestiary.json';
import jpmCatalog from '../data/jinpingmei.bestiary.json';
import xyjCatalog from '../data/xiyouji.bestiary.json';

export type BestiaryCatalog = {
  book: string;
  groups?: Record<string, string[]>;
  fields?: Record<string, unknown>;
};

export type BestiarySection<T> = { label: string; items: T[] };

export const BESTIARY_CATALOGS: Record<string, BestiaryCatalog> = {
  honglou: hlmCatalog as BestiaryCatalog,
  jinpingmei: jpmCatalog as BestiaryCatalog,
  xiyouji: xyjCatalog as BestiaryCatalog,
};

const FACTION_ORDER: Record<string, readonly string[]> = {
  jinpingmei: ['西门府', '帮闲圈', '清河县', '朝廷'],
  xiyouji: ['取经队伍', '天界', '佛界', '仙界', '龙宫', '大唐', '西梁女国', '妖魔'],
};

/** 按 catalog.groups 顺序分组；未列入者归入 restLabel */
export function groupByCatalog<T extends { data: { id: string } }>(
  list: T[],
  groups: Record<string, string[]>,
  restLabel = '其他',
): BestiarySection<T>[] {
  const byId = new Map(list.map((e) => [e.data.id, e]));
  const used = new Set<string>();
  const result: BestiarySection<T>[] = [];

  for (const [label, ids] of Object.entries(groups)) {
    const items = ids.map((id) => byId.get(id)).filter(Boolean) as T[];
    if (items.length === 0) continue;
    items.forEach((e) => used.add(e.data.id));
    result.push({ label, items });
  }

  const rest = list.filter((e) => !used.has(e.data.id));
  if (rest.length > 0) result.push({ label: restLabel, items: rest });
  return result;
}

/** 按 faction 分组（无 catalog 时的回退） */
export function groupByFaction<T extends { data: { id: string; faction?: string } }>(
  list: T[],
  bookSlug: string,
): BestiarySection<T>[] {
  const order = FACTION_ORDER[bookSlug] ?? [];
  const map = new Map<string, T[]>();
  for (const e of list) {
    const f = e.data.faction ?? '其他';
    if (!map.has(f)) map.set(f, []);
    map.get(f)!.push(e);
  }
  const keys = [...map.keys()].sort((a, b) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    const ai = ia === -1 ? 999 : ia;
    const bi = ib === -1 ? 999 : ib;
    return ai - bi || a.localeCompare(b, 'zh-CN');
  });
  return keys.map((label) => ({ label, items: map.get(label)! }));
}

export function resolveBestiarySections<T extends { data: { id: string; faction?: string } }>(
  bookSlug: string,
  list: T[],
): BestiarySection<T>[] {
  const catalog = BESTIARY_CATALOGS[bookSlug];
  const restLabel = bookSlug === 'honglou' ? '其他人物' : bookSlug === 'xiyouji' ? '其他' : '其他';
  if (catalog?.groups && Object.keys(catalog.groups).length > 0) {
    return groupByCatalog(list, catalog.groups, restLabel);
  }
  return groupByFaction(list, bookSlug);
}

export type BestiaryStats = {
  total: number;
  groupCount: number;
  /** 金瓶梅 */
  withBacking?: number;
  withOutcome?: number;
  /** 红楼梦 */
  withPersonality?: number;
  withLikes?: number;
  /** 西游记 */
  monsterCount?: number;
  characterCount?: number;
};

export function bestiaryStatsFor(
  bookSlug: string,
  entries: { data: { type: string; 靠山?: string; 结局?: string; 性格?: string; 喜好?: string[] } }[],
): BestiaryStats {
  const sections = resolveBestiarySections(
    bookSlug,
    entries as { data: { id: string; faction?: string } }[],
  );
  const base: BestiaryStats = {
    total: entries.length,
    groupCount: sections.length,
  };
  if (bookSlug === 'jinpingmei') {
    const chars = entries.filter((e) => e.data.type === 'character');
    return {
      ...base,
      withBacking: chars.filter((e) => e.data.靠山).length,
      withOutcome: chars.filter((e) => e.data.结局).length,
      withPersonality: chars.filter((e) => e.data.性格).length,
      withLikes: chars.filter((e) => (e.data.喜好?.length ?? 0) > 0).length,
    };
  }
  if (bookSlug === 'honglou') {
    const chars = entries.filter((e) => e.data.type === 'character');
    return {
      ...base,
      withPersonality: chars.filter((e) => e.data.性格).length,
      withLikes: chars.filter((e) => (e.data.喜好?.length ?? 0) > 0).length,
    };
  }
  if (bookSlug === 'xiyouji') {
    return {
      ...base,
      characterCount: entries.filter((e) => e.data.type === 'character').length,
      monsterCount: entries.filter((e) => e.data.type === 'monster').length,
      withPersonality: entries.filter((e) => e.data.性格).length,
      withLikes: entries.filter((e) => (e.data.喜好?.length ?? 0) > 0).length,
    };
  }
  return base;
}
