/** 图鉴 · 喜好项是否可链至名物页 */

import hlmItemIds from '../data/hongloumeng.item_ids.json';
import xyjItemIds from '../data/xiyouji.item_ids.json';

const ITEM_IDS: Record<string, Set<string>> = {
  honglou: new Set(hlmItemIds as string[]),
  xiyouji: new Set(xyjItemIds as string[]),
};

export function likeItemHref(bookSlug: string, like: string): string | null {
  const ids = ITEM_IDS[bookSlug];
  if (!ids?.has(like)) return null;
  return `/${bookSlug}/i/${encodeURIComponent(like)}`;
}
