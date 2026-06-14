import type { CollectionEntry } from 'astro:content';

/** 与 src/content/books/*.md frontmatter 同步；content store 不可用时作路由兜底 */
export type BookData = CollectionEntry<'books'>['data'];

export const BOOKS_CATALOG: BookData[] = [
  {
    book: '红楼梦',
    slug: 'honglou',
    author: '曹雪芹',
    chapter_count: 120,
    features: ['reader', 'graph', 'poems', 'items', 'places', 'bestiary', 'kaozheng'],
    summary: '以贾府兴衰与宝黛爱情为主线的章回体长篇小说，存脂评本与程高本异文。',
  },
  {
    book: '西游记',
    slug: 'xiyouji',
    author: '吴承恩',
    chapter_count: 100,
    features: ['reader', 'graph', 'bestiary', 'items', 'nan', 'route', 'quanshi', 'kaozheng'],
    summary: '唐僧师徒四人西天取经，历经九九八十一难的神魔小说。',
  },
  {
    book: '金瓶梅',
    slug: 'jinpingmei',
    author: '兰陵笑笑生',
    chapter_count: 100,
    features: ['reader', 'graph', 'bestiary', 'places', 'silver', 'items', 'sna', 'compare', 'chain', 'kaozheng'],
    summary: '借《水浒》西门庆故事敷演而成的世情小说，写市井家庭兴衰。正文来自殆知阁词话本。',
  },
];

export function catalogBookBySlug(slug: string): BookData | undefined {
  return BOOKS_CATALOG.find((b) => b.slug === slug);
}
