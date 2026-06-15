/** 图鉴分组 · 三书共用 catalog 模式 */

import { cardOutcome } from './bestiary';
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
  entries: {
    data: {
      type: string;
      靠山?: string;
      结局?: string;
      性格?: string;
      喜好?: string[];
      arc?: { chapter?: number; stage?: string; title?: string; note?: string }[];
      summary?: string;
    };
  }[],
): BestiaryStats {
  const withOutcomeCount = entries.filter((e) => cardOutcome(e.data) ?? e.data.结局).length;
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
      withOutcome: withOutcomeCount,
      withPersonality: chars.filter((e) => e.data.性格).length,
      withLikes: chars.filter((e) => (e.data.喜好?.length ?? 0) > 0).length,
    };
  }
  if (bookSlug === 'honglou') {
    return {
      ...base,
      withPersonality: entries.filter((e) => e.data.性格).length,
      withLikes: entries.filter((e) => (e.data.喜好?.length ?? 0) > 0).length,
      withOutcome: withOutcomeCount,
    };
  }
  if (bookSlug === 'xiyouji') {
    return {
      ...base,
      characterCount: entries.filter((e) => e.data.type === 'character').length,
      monsterCount: entries.filter((e) => e.data.type === 'monster').length,
      withPersonality: entries.filter((e) => e.data.性格).length,
      withLikes: entries.filter((e) => (e.data.喜好?.length ?? 0) > 0).length,
      withOutcome: withOutcomeCount,
    };
  }
  return base;
}

/* ───────────────────────── 多维分组（切换器） ───────────────────────── */

/** 可参与多维分组的人物条目（字段均可选） */
export type GroupableEntry = {
  data: {
    id: string;
    type?: string;
    faction?: string;
    status?: string;
    weight?: number;
    ximen_proximity?: string;
    first_appear?: string;
    结局?: string;
  };
};

/** 额外数据源：由页面注入（如 SNA 中心度） */
export type GroupingContext = {
  /** id → degree_norm（0~1），来自 src/data/<slug>.sna.json */
  centrality?: Map<string, number>;
};

/** 一种分组依据：key 用于切换、label 用于 tab、sections 为预渲染分区 */
export type BestiaryGrouping<T> = {
  key: string;
  label: string;
  sections: BestiarySection<T>[];
};

/** 通用按键分组：keyFn 取分组键，order 定义顺序，未命中→末尾，空值→restLabel */
function groupByKey<T extends { data: { id: string } }>(
  list: T[],
  keyFn: (e: T) => string | undefined,
  order: readonly string[],
  restLabel: string,
): BestiarySection<T>[] {
  const map = new Map<string, T[]>();
  for (const e of list) {
    const k = keyFn(e) || restLabel;
    if (!map.has(k)) map.set(k, []);
    map.get(k)!.push(e);
  }
  const rank = (label: string) => {
    if (label === restLabel) return 999;
    const i = order.indexOf(label);
    return i === -1 ? 998 : i;
  };
  return [...map.keys()]
    .sort((a, b) => rank(a) - rank(b) || a.localeCompare(b, 'zh-CN'))
    .map((label) => ({ label, items: map.get(label)! }));
}

const STATUS_ORDER = ['主角', '重要', '配角'] as const;

const PROX_LABEL: Record<string, string> = {
  亲缘: '亲缘 · 西门府内',
  雇佣: '雇佣 · 仆佣',
  利益交换: '利益交换 · 帮闲商贾',
  外人: '外人 · 远端',
};
const PROX_ORDER = Object.values(PROX_LABEL);

const OUTCOME_RULES: [string, RegExp][] = [
  ['出家 / 遁世', /出家|遁入空门|为僧|为尼|做道士|出世|遁世/],
  ['横死 / 被害', /杀|害死|被害|凌迟|处死|自缢|自尽|投井|溺|惨死|暴亡|斩|阵亡|殒命/],
  ['早逝 / 病亡', /病亡|病死|夭|早亡|早逝|血崩|气病|脱阳|殁|卒/],
  ['被卖 / 流放', /卖|发配|流放|拐|远遁|充军/],
  ['出嫁 / 改嫁', /改嫁|出嫁|嫁/],
  ['守业 / 显贵', /善终|寿终|得贵|显贵|封诰|荣养|富贵|守寡|持家|得势/],
];
const OUTCOME_ORDER = OUTCOME_RULES.map(([label]) => label);

function classifyOutcome(text?: string): string | undefined {
  if (!text) return undefined;
  for (const [label, re] of OUTCOME_RULES) if (re.test(text)) return label;
  return '其他归宿';
}

/* —— SNA 中心度（按 degree_norm 分层） —— */
const CENTRALITY_ORDER = ['核心枢纽', '主要节点', '次要节点', '边缘节点'] as const;
function centralityTier(d?: number): string | undefined {
  if (d == null) return undefined; // 不在图谱 → restLabel
  if (d >= 0.5) return '核心枢纽';
  if (d >= 0.15) return '主要节点';
  if (d >= 0.05) return '次要节点';
  return '边缘节点';
}

/* —— 首次登场回段（每 20 回一段） —— */
const CHAPTER_BUCKET_ORDER = [
  '第 1–20 回',
  '第 21–40 回',
  '第 41–60 回',
  '第 61–80 回',
  '第 81–100 回',
  '第 101–120 回',
] as const;
function chapterBucket(fa?: string): string | undefined {
  if (!fa) return undefined;
  const m = fa.match(/(\d+)/);
  if (!m) return undefined;
  const n = Number(m[1]);
  if (!Number.isFinite(n) || n <= 0) return undefined;
  const lo = Math.floor((n - 1) / 20) * 20 + 1;
  return `第 ${lo}–${lo + 19} 回`;
}

/* —— 红楼 · 神话双层（太虚 / 人间） —— */
const HLM_CELESTIAL = new Set([
  '神瑛侍者',
  '绛珠仙子',
  '绛珠仙草',
  '警幻仙子',
  '警幻仙姑',
  '渺渺真人',
  '茫茫大士',
  '空空道人',
  '一僧一道',
]);
const MYTH_LAYER_ORDER = ['太虚幻境 · 神话层', '人间贾府 · 现世层'] as const;
function mythLayer(id: string): string {
  return HLM_CELESTIAL.has(id) ? '太虚幻境 · 神话层' : '人间贾府 · 现世层';
}

/* —— 红楼 · 镜像配对（脂评「真身 / 影身」说） —— */
const HLM_MIRRORS: { label: string; ids: string[] }[] = [
  { label: '黛玉系 · 真身与影（晴为黛影）', ids: ['林黛玉', '晴雯', '龄官'] },
  { label: '宝钗系 · 真身与影（袭为钗副）', ids: ['薛宝钗', '袭人', '麝月'] },
];
const MIRROR_ORDER = HLM_MIRRORS.map((m) => m.label);
const MIRROR_OF = new Map<string, string>();
for (const m of HLM_MIRRORS) for (const id of m.ids) MIRROR_OF.set(id, m.label);

/**
 * 构建一本书可用的全部分组依据（首项恒为「身份名册」）。
 * 仅当某维度字段覆盖度足够时才提供该分组，避免出现整页「其他」。
 */
export function buildBestiaryGroupings<T extends GroupableEntry & { data: { faction?: string } }>(
  bookSlug: string,
  list: T[],
  ctx: GroupingContext = {},
): BestiaryGrouping<T>[] {
  const out: BestiaryGrouping<T>[] = [];
  const enough = (n: number) => n >= Math.max(6, Math.ceil(list.length * 0.3));
  const cover = (fn: (e: T) => unknown) => list.filter((e) => fn(e)).length;

  // 1) 身份名册（catalog；无 groups 时回退 faction）—— 恒在
  out.push({ key: 'catalog', label: '身份名册', sections: resolveBestiarySections(bookSlug, list) });

  // 2) 与西门府距离（金瓶专属）
  if (bookSlug === 'jinpingmei' && cover((e) => e.data.ximen_proximity) >= 3) {
    out.push({
      key: 'proximity',
      label: '与西门府距离',
      sections: groupByKey(list, (e) => PROX_LABEL[e.data.ximen_proximity ?? ''], PROX_ORDER, '未标距离'),
    });
  }

  // 3) SNA 中心度（依赖 <slug>.sna.json 注入）
  const centrality = ctx.centrality;
  if (centrality && cover((e) => centrality.has(e.data.id)) >= 6) {
    out.push({
      key: 'centrality',
      label: 'SNA 中心度',
      sections: groupByKey(list, (e) => centralityTier(centrality.get(e.data.id)), CENTRALITY_ORDER, '未入图谱'),
    });
  }

  // 4) 命运归宿（三书通用，依赖 结局 覆盖度）
  if (enough(cover((e) => e.data.结局))) {
    out.push({
      key: 'outcome',
      label: '命运归宿',
      sections: groupByKey(list, (e) => classifyOutcome(e.data.结局), OUTCOME_ORDER, '归宿未明'),
    });
  }

  // 5) 重要度（依赖 status 覆盖度）
  if (enough(cover((e) => e.data.status))) {
    out.push({
      key: 'status',
      label: '重要度',
      sections: groupByKey(list, (e) => e.data.status, STATUS_ORDER, '其他'),
    });
  }

  // 6) 首次登场回段（依赖 first_appear 覆盖度）
  if (enough(cover((e) => e.data.first_appear))) {
    out.push({
      key: 'debut',
      label: '首次登场',
      sections: groupByKey(list, (e) => chapterBucket(e.data.first_appear), CHAPTER_BUCKET_ORDER, '未标回目'),
    });
  }

  // 7) 家族 / 阵营（依赖 faction 覆盖度，作为 catalog 的另一视角）
  if (enough(cover((e) => e.data.faction))) {
    out.push({ key: 'faction', label: '家族 / 阵营', sections: groupByFaction(list, bookSlug) });
  }

  // 8) 神话双层（红楼专属：太虚 / 人间）
  if (bookSlug === 'honglou' && cover((e) => HLM_CELESTIAL.has(e.data.id)) >= 2) {
    out.push({
      key: 'myth',
      label: '神话双层',
      sections: groupByKey(list, (e) => mythLayer(e.data.id), MYTH_LAYER_ORDER, '人间贾府 · 现世层'),
    });
  }

  // 9) 镜像配对（红楼专属：脂评真身 / 影身）
  if (bookSlug === 'honglou' && cover((e) => MIRROR_OF.has(e.data.id)) >= 2) {
    out.push({
      key: 'mirror',
      label: '镜像配对',
      sections: groupByKey(list, (e) => MIRROR_OF.get(e.data.id), MIRROR_ORDER, '未列镜像'),
    });
  }

  return out;
}
