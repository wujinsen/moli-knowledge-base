/** 图鉴 · 喜好项是否可链至名物页 */

import hlmItemIds from '../data/hongloumeng.item_ids.json';
import xyjItemIds from '../data/xiyouji.item_ids.json';

const ITEM_IDS: Record<string, Set<string>> = {
  honglou: new Set(hlmItemIds as string[]),
  xiyouji: new Set(xyjItemIds as string[]),
};

export type CardArcNode = {
  chapter?: number;
  stage?: string;
  title?: string;
  note?: string;
};

export type CardCharacterData = {
  结局?: string;
  arc?: CardArcNode[];
  summary?: string;
};

/** 图鉴卡片「结局」：优先 frontmatter，其次 arc 结局节点 */
export function cardOutcome(data: CardCharacterData): string | undefined {
  const explicit = data.结局?.trim();
  if (explicit) return explicit;
  const arc = data.arc ?? [];
  for (let i = arc.length - 1; i >= 0; i -= 1) {
    const node = arc[i];
    if (node.stage === '结局') {
      const title = node.title?.trim();
      const note = node.note?.trim();
      const ch = node.chapter;
      const suffix = ch != null ? `（第${ch}回）` : '';
      if (title) return `${title}${suffix}`;
      if (note) return note.length > 56 ? `${note.slice(0, 56)}…` : note;
    }
  }
  return undefined;
}

export function likeItemHref(bookSlug: string, like: string): string | null {
  const ids = ITEM_IDS[bookSlug];
  if (!ids?.has(like)) return null;
  return `/${bookSlug}/i/${encodeURIComponent(like)}`;
}

/** 图鉴 chip：名物优先，其次地点 */
export function chipHref(
  bookSlug: string,
  label: string,
  placeIds?: ReadonlySet<string>,
): string | null {
  const item = likeItemHref(bookSlug, label);
  if (item) return item;
  if (placeIds?.has(label)) {
    return `/${bookSlug}/l/${encodeURIComponent(label)}`;
  }
  return null;
}

/** 服饰 / 关键物品等同理链至名物百科 */
export const itemWikiHref = likeItemHref;

/** 人物 frontmatter `关键物品` 的展示标签（按书 slug） */
export function keyItemsLabel(bookSlug: string): string {
  return bookSlug === 'honglou' ? '信物' : '关键物品';
}
