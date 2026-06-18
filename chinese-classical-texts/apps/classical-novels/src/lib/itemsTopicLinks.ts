/** B7/C4 名物 ↔ 纵切主题页互链（build_items_cross_index.py 生成） */

import honglouTopicsJson from '../data/hongloumeng.items_topics.json';
import jpmTopicsJson from '../data/jinpingmei.items_topics.json';

export interface ItemTopicLink {
  title: string;
  slug: string;
}

type ItemsTopicsFile = {
  book: string;
  links: Record<string, ItemTopicLink[]>;
};

const TOPICS_BY_SLUG: Record<string, ItemsTopicsFile> = {
  honglou: honglouTopicsJson as ItemsTopicsFile,
  jinpingmei: jpmTopicsJson as ItemsTopicsFile,
};

export function getItemTopicLinks(bookSlug: string, itemId: string): ItemTopicLink[] {
  return TOPICS_BY_SLUG[bookSlug]?.links[itemId] ?? [];
}

/** 红楼梦纵切主题 hub（手工维护，items 页展示） */
export const HONGLOU_ITEM_TOPIC_HUB: ItemTopicLink[] = [
  { title: '饮食纵切总览', slug: '饮食纵切总览' },
  { title: '医药饮食名录', slug: '医药饮食名录' },
  { title: '医药诊脉链', slug: '医药诊脉链' },
  { title: '图鉴名物信物链总览', slug: '图鉴名物信物链总览' },
  { title: '十二钗名物纵切', slug: '十二钗名物纵切' },
  { title: '露剂与家法链', slug: '露剂与家法链' },
  { title: '元宵年例链', slug: '元宵年例链' },
];

/** 金瓶梅物质纵切主题 hub（C4 J2） */
export const JPM_ITEM_TOPIC_HUB: ItemTopicLink[] = [
  { title: '西门府建筑名录', slug: '西门府建筑名录' },
  { title: '版本对勘样本', slug: '版本对勘样本' },
  { title: '世情与贵族衰败对比', slug: '世情与贵族衰败对比' },
  { title: '药铺与放债链', slug: '药铺与放债链' },
];

export function itemTopicHubForBook(bookSlug: string): ItemTopicLink[] {
  if (bookSlug === 'honglou') return HONGLOU_ITEM_TOPIC_HUB;
  if (bookSlug === 'jinpingmei') return JPM_ITEM_TOPIC_HUB;
  return [];
}
