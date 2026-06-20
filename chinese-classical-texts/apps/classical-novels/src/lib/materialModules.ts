/** 名物四分类 + 法宝 · 模块路由与 Hub 配置 */

import type { ItemKind } from './itemsKind';
import { kindLabel } from './itemsKind';

export type MaterialModuleKey = 'food' | 'medicine' | 'costume' | 'custom' | 'artifacts';

export interface MaterialModuleDef {
  key: MaterialModuleKey;
  kind: ItemKind;
  glyph: string;
  title: string;
  desc: string;
  feature: MaterialModuleKey;
  /** 纵切主题 slug 子集（空=不展示主题区） */
  topicSlugs?: string[];
}

const MODULES: MaterialModuleDef[] = [
  {
    key: 'food',
    kind: 'dish',
    glyph: '膳',
    title: '饮食',
    desc: '菜品 · 宴席 · 茶酒 · 膳食推演',
    feature: 'food',
    topicSlugs: ['饮食纵切总览'],
  },
  {
    key: 'medicine',
    kind: 'medicine',
    glyph: '医',
    title: '医药',
    desc: '方剂 · 诊脉 · 脉案互证',
    feature: 'medicine',
    topicSlugs: ['医药饮食名录', '医药诊脉链', '医药病理与社会四病灶', '露剂与家法链'],
  },
  {
    key: 'costume',
    kind: 'costume',
    glyph: '衣',
    title: '服饰',
    desc: '织品 · 首饰 · 穿戴场合',
    feature: 'costume',
    topicSlugs: ['十二钗名物纵切', '图鉴名物信物链总览', '服饰精神面貌与社会四横切面'],
  },
  {
    key: 'custom',
    kind: 'custom',
    glyph: '俗',
    title: '民俗',
    desc: '礼仪 · 制度 · 节令规章',
    feature: 'custom',
    topicSlugs: ['元宵年例链', '民俗状态与社会四横切面'],
  },
  {
    key: 'artifacts',
    kind: 'artifact',
    glyph: '宝',
    title: '法宝谱系',
    desc: '制造 · 持有 · 克制关系',
    feature: 'artifacts',
    topicSlugs: ['法宝谱系总览'],
  },
];

const JPM_EXTRA_TOPICS = ['西门府建筑名录', '版本对勘样本', '世情与贵族衰败对比'];

/** 各书纵切主题：存在 topics/<书>/ 下的 slug；未列书目则用 MODULES 默认（红楼） */
const BOOK_MODULE_TOPICS: Partial<
  Record<string, Partial<Record<MaterialModuleKey, string[]>>>
> = {
  jinpingmei: {
    food: ['药铺与放债链', '帮闲圈分析', '世情四横切面与社会推演'],
    medicine: ['药铺与放债链', '方外人物群', '世情四横切面与社会推演'],
    costume: [],
    custom: ['帮闲圈分析', '世情四横切面与社会推演'],
  },
};

export function hasMaterialFeature(features: string[], key: MaterialModuleKey): boolean {
  if (features.includes(key)) return true;
  if (key === 'artifacts') return features.includes('items');
  return features.includes('items');
}

export function materialModulesForBook(bookSlug: string, features: string[]): MaterialModuleDef[] {
  if (bookSlug === 'xiyouji') {
    return MODULES.filter((m) => m.key === 'artifacts' && hasMaterialFeature(features, 'artifacts'));
  }
  return MODULES.filter((m) => m.key !== 'artifacts' && hasMaterialFeature(features, m.key));
}

export function materialModuleHref(bookSlug: string, key: MaterialModuleKey): string {
  if (key === 'artifacts') return `/${bookSlug}/artifacts`;
  return `/${bookSlug}/${key}`;
}

export function materialHubHref(bookSlug: string): string {
  return `/${bookSlug}/items`;
}

export function materialCrossIndexHref(bookSlug: string): string {
  return `/${bookSlug}/items/cross`;
}

export function materialFoodInferenceHref(bookSlug: string): string {
  return `/${bookSlug}/food/inference`;
}

export function materialInferenceHref(bookSlug: string, key: MaterialModuleKey): string | null {
  if (key === 'food') return materialFoodInferenceHref(bookSlug);
  if (key === 'medicine' || key === 'costume' || key === 'custom') {
    return `/${bookSlug}/${key}/inference`;
  }
  return null;
}

export function materialInferenceLabel(key: MaterialModuleKey): string | null {
  const labels: Partial<Record<MaterialModuleKey, string>> = {
    food: '膳食推演',
    medicine: '药疗推演',
    costume: '服饰推演',
    custom: '民俗推演',
  };
  return labels[key] ?? null;
}

/** 详情页返回对应分类模块 */
export function catalogHrefForKind(bookSlug: string, kind: ItemKind): string {
  const mod = MODULES.find((m) => m.kind === kind);
  if (!mod) return materialHubHref(bookSlug);
  return materialModuleHref(bookSlug, mod.key);
}

export function catalogLabelForKind(kind: ItemKind): string {
  return kindLabel(kind);
}

function effectiveTopicSlugs(bookSlug: string, key: MaterialModuleKey): string[] {
  const override = BOOK_MODULE_TOPICS[bookSlug]?.[key];
  if (override !== undefined) return override;
  return MODULES.find((m) => m.key === key)?.topicSlugs ?? [];
}

export function topicHubForModule(bookSlug: string, key: MaterialModuleKey): { title: string; slug: string }[] {
  return effectiveTopicSlugs(bookSlug, key).map((slug) => ({ slug, title: slug }));
}

export function materialModuleTitle(key: MaterialModuleKey): string {
  return MODULES.find((m) => m.key === key)?.title ?? key;
}

/**
 * 反查纵切主题所属物质模块；仅当**唯一**模块拥有该主题时返回，
 * 跨切面主题（多个模块共享）返回 null，交由历史返回兜底。
 */
export function moduleForTopicSlug(bookSlug: string, slug: string): MaterialModuleKey | null {
  const owners = MODULES.filter((m) => effectiveTopicSlugs(bookSlug, m.key).includes(slug)).map(
    (m) => m.key,
  );
  return owners.length === 1 ? owners[0] : null;
}

export interface MaterialCrumb {
  href?: string;
  label: string;
}

/**
 * 物质模块子树面包屑：名物百科 › 模块[ › 推演 / 主题]
 * - `hubLabel`：hub 显示名（西游记为「法宝谱系」，默认「名物百科」）
 * - 当 hub 名与单一模块名相同（西游记 法宝谱系）时，用书首页代替 hub 以免重复
 */
export function materialCrumbs(
  bookSlug: string,
  key: MaterialModuleKey,
  opts: {
    view: 'catalog' | 'inference' | 'topic';
    topicTitle?: string;
    hubLabel?: string;
    bookName?: string;
  },
): MaterialCrumb[] {
  const hubLabel = opts.hubLabel ?? '名物百科';
  const title = materialModuleTitle(key);
  const parent: MaterialCrumb =
    title === hubLabel && opts.bookName
      ? { href: `/${bookSlug}`, label: opts.bookName }
      : { href: materialHubHref(bookSlug), label: hubLabel };
  const crumbs: MaterialCrumb[] = [parent];
  if (opts.view === 'catalog') {
    crumbs.push({ label: title });
    return crumbs;
  }
  crumbs.push({ href: materialModuleHref(bookSlug, key), label: title });
  if (opts.view === 'inference') {
    crumbs.push({ label: materialInferenceLabel(key) ?? '推演' });
  } else {
    crumbs.push({ label: opts.topicTitle ?? '主题' });
  }
  return crumbs;
}

export function hubExtraTopics(bookSlug: string): { title: string; slug: string }[] {
  if (bookSlug === 'jinpingmei') {
    return JPM_EXTRA_TOPICS.map((slug) => ({ slug, title: slug }));
  }
  return [];
}

/** 旧 /diet 深链 → 食物推演 */
export function legacyDietHref(bookSlug: string, chapter?: number): string {
  const base = materialFoodInferenceHref(bookSlug);
  return chapter != null ? `${base}?chapter=${chapter}` : base;
}
