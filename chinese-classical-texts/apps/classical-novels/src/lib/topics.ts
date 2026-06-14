import { getCollection, type CollectionEntry } from 'astro:content';

export type TopicEntry = CollectionEntry<'topics'>;

/** glob loader 的 id 形如「西游记/狮驼岭三魔总览」；取末段作为书内 slug */
export function topicSlug(entry: TopicEntry): string {
  const parts = entry.id.split('/');
  return parts[parts.length - 1];
}

export function topicHref(bookSlug: string, entry: TopicEntry): string {
  return `/${bookSlug}/topics/${topicSlug(entry)}`;
}

/** 考证台分支固定顺序 */
export const KAOZHENG_BRANCHES = ['成书史', '版本学', '作者公案'] as const;
export type KaozhengBranch = (typeof KAOZHENG_BRANCHES)[number];

/** 诠释视角固定顺序 + 单字标记 */
export const QUANSHI_LENSES = ['内丹', '政治', '原型', '民俗', '叙事', '宗教'] as const;
export type QuanshiLens = (typeof QUANSHI_LENSES)[number];

export const LENS_GLYPH: Record<string, string> = {
  内丹: '丹',
  政治: '政',
  原型: '源',
  民俗: '俗',
  叙事: '叙',
  宗教: '禅',
};

export const BRANCH_GLYPH: Record<string, string> = {
  成书史: '源',
  版本学: '勘',
  作者公案: '考',
};

export const STANCE_LABEL: Record<string, string> = {
  主流: '主流说',
  存疑: '存疑',
  少数: '少数说',
  已弃: '已弃',
};

/** 加载某书全部 topic */
export async function loadTopics(book: string): Promise<TopicEntry[]> {
  const all = await getCollection('topics');
  return all.filter((t) => t.data.book === book);
}

export function byCategory(topics: TopicEntry[], category: string): TopicEntry[] {
  return topics.filter((t) => t.data.category === category);
}

/** 按考证分支分组（固定顺序，空组省略） */
export function groupByBranch(topics: TopicEntry[]): { branch: KaozhengBranch; items: TopicEntry[] }[] {
  return KAOZHENG_BRANCHES.map((branch) => ({
    branch,
    items: topics.filter((t) => t.data.branch === branch),
  })).filter((g) => g.items.length > 0);
}

/** 按诠释视角分组（固定顺序，空组省略） */
export function groupByLens(topics: TopicEntry[]): { lens: QuanshiLens; items: TopicEntry[] }[] {
  return QUANSHI_LENSES.map((lens) => ({
    lens,
    items: topics.filter((t) => t.data.lens === lens),
  })).filter((g) => g.items.length > 0);
}

/** 汇总一组 topic 的全部假说卡，带来源 topic 引用 */
export function collectHypotheses(topics: TopicEntry[]) {
  const out: {
    topic: TopicEntry;
    claim: string;
    proponent?: string;
    period?: string;
    stance: string;
    evidence: string[];
    counter?: string;
    source?: string;
  }[] = [];
  for (const t of topics) {
    for (const h of t.data.hypotheses) {
      out.push({ topic: t, ...h });
    }
  }
  return out;
}
