/** D6：西游记五行生克 · 修心网络（build_shi_wuxing.py 生成） */

import wuxingJson from '../data/xiyouji.shi-wuxing.json';

export type WuxingElement = '金' | '木' | '土' | '水' | '火';
export type WuxingRelation = '相克' | '交并' | '调和' | '相济';

export interface WuxingNode {
  id: string;
  title: string;
  characters: string[];
}

export interface WuxingEdge {
  source: string;
  target: string;
  sourceTitle: string;
  targetTitle: string;
  sourceElement?: WuxingElement | null;
  targetElement?: WuxingElement | null;
  predicate: WuxingRelation;
  chapter?: number | null;
  note?: string | null;
}

export interface WuxingChain {
  id: string;
  name: string;
  summary?: string;
  path: string[];
}

export interface ShiWuxingData {
  book: string;
  slug: string;
  elements: WuxingElement[];
  by_element: Record<WuxingElement, WuxingNode[]>;
  element_counts: Record<WuxingElement, number>;
  edges: WuxingEdge[];
  relation_counts: Record<WuxingRelation, number>;
  chains: WuxingChain[];
}

const WUXING = wuxingJson as ShiWuxingData;

export const WUXING_ELEMENTS: WuxingElement[] = ['金', '木', '土', '水', '火'];
export const WUXING_RELATIONS: WuxingRelation[] = ['相克', '交并', '调和', '相济'];

/** 五行对应色（金白 / 木青 / 土黄 / 水玄 / 火赤），用于节点描边 */
export const ELEMENT_COLOR: Record<WuxingElement, string> = {
  金: '#b8923a',
  木: '#3f7d4f',
  土: '#a9762e',
  水: '#355766',
  火: '#c0432b',
};

/** 生克关系语义色：相克/交并(金木) 暖 · 调和(土) 中 · 相济(水火) 冷 */
export const RELATION_COLOR: Record<WuxingRelation, string> = {
  相克: '#c0432b',
  交并: '#b8923a',
  调和: '#a9762e',
  相济: '#355766',
};

export function getShiWuxing(bookSlug: string): ShiWuxingData | null {
  return bookSlug === 'xiyouji' ? WUXING : null;
}
