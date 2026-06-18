/** B7 名物 ↔ 纵切主题页互链（build_items_cross_index.py 生成） */

import itemsTopicsJson from '../data/hongloumeng.items_topics.json';

export interface ItemTopicLink {
  title: string;
  slug: string;
}

type ItemsTopicsFile = {
  book: string;
  links: Record<string, ItemTopicLink[]>;
};

const TOPICS = itemsTopicsJson as ItemsTopicsFile;

export function getItemTopicLinks(itemId: string): ItemTopicLink[] {
  return TOPICS.links[itemId] ?? [];
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

export function itemTopicHubForBook(bookSlug: string): ItemTopicLink[] {
  return bookSlug === 'honglou' ? HONGLOU_ITEM_TOPIC_HUB : [];
}
