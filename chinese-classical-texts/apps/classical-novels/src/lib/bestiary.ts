/** 图鉴 · 喜好项是否可链至名物页 */

import hlmItemIds from '../data/hongloumeng.item_ids.json';

const HLM_ITEM_IDS = new Set(hlmItemIds as string[]);

export function likeItemHref(bookSlug: string, like: string): string | null {
  if (bookSlug !== 'honglou') return null;
  if (!HLM_ITEM_IDS.has(like)) return null;
  return `/${bookSlug}/i/${encodeURIComponent(like)}`;
}
