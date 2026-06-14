import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

export const BOOKS = ['红楼梦', '金瓶梅', '西游记'] as const;

export const RELATION_TYPES = [
  // 亲属
  '夫妻', '父子', '母子', '兄弟', '姐妹', '祖孙', '妯娌',
  // 社会
  '主仆', '师徒', '师兄弟', '同僚', '朋友', '结拜', '君臣',
  // 情感
  '情人', '恋慕', '仇敌', '敌对',
  // 金瓶梅 · 利益与府内
  '帮闲', '贿赂', '借贷', '认干亲', '庇护', '资助', '嫉妒', '陷害',
] as const;

export const XIMEN_PROXIMITY = ['亲缘', '雇佣', '利益交换', '外人'] as const;

const relation = z.object({
  target: z.string(),
  type: z.enum(RELATION_TYPES),
  role: z.string().optional(),
});

const variant = z.object({
  edition: z.string(),
  claim: z.string(),
  source: z.string().optional(),
});

const characters = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/characters' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['character', 'monster']),
    name: z.string(),
    aliases: z.array(z.string()).default([]),
    gender: z.string().optional(),
    book: z.enum(BOOKS),
    faction: z.string().optional(),
    first_appear: z.string().optional(),
    status: z.enum(['主角', '重要', '配角']).optional(),
    tags: z.array(z.string()).default([]),
    // 金瓶梅 · 与西门府利益距离
    ximen_proximity: z.enum(XIMEN_PROXIMITY).optional(),
    // 妖怪扩展字段
    洞府: z.string().optional(),
    原型: z.string().optional(),
    能力: z.array(z.string()).default([]),
    法宝: z.array(z.string()).default([]),
    结局: z.string().optional(),
    收服者: z.string().optional(),
    // 关系与版本
    relations: z.array(relation).default([]),
    variants: z.array(variant).default([]),
    contradicts: z.array(z.string()).default([]),
    // 由 /consolidate 重算，勿手填
    weight: z.number().min(0).max(100).optional(),
    summary: z.string().optional(),
  }),
});

const chapters = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/chapters' }),
  schema: z.object({
    type: z.literal('chapter'),
    book: z.enum(BOOKS),
    number: z.number(),
    title: z.string(),
    // 版本（坑3：跨版本同名，检索/异文必须可区分）。如「程高本」「词话本」「绣像本」。
    edition: z.string().optional(),
    // 原文来源路径（指回 raw，只读真相源）
    source: z.string().optional(),
    characters: z.array(z.string()).default([]),
    locations: z.array(z.string()).default([]),
    items: z.array(z.string()).default([]),
    summary: z.string().optional(),
  }),
});

const books = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/books' }),
  schema: z.object({
    book: z.enum(BOOKS),
    slug: z.string(),
    author: z.string(),
    chapter_count: z.number(),
    features: z.array(
      z.enum(['reader', 'graph', 'bestiary', 'items', 'poems', 'places', 'silver', 'sna', 'nan', 'route'])
    ),
    summary: z.string().optional(),
  }),
});

const LOCATION_CATEGORIES = [
  '府邸', '花园', '院落', '亭', '楼', '阁', '榭', '堂', '馆', '庵', '祠', '闸', '幻境', '市街',
  // 西游记 · 取经地理
  '国度', '山岭', '洞府', '水域', '天界', '地府', '仙山', '城关', '寺观',
  '其他',
] as const;

// 西游记取经路线 GIS：地理分层（real 凡间路线 / myth 神话异界）
const ROUTE_LAYERS = ['real', 'myth'] as const;

const locations = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/locations' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['location', 'building', 'garden', 'temple', 'realm']),
    name: z.string(),
    aliases: z.array(z.string()).default([]),
    book: z.enum(BOOKS),
    category: z.enum(LOCATION_CATEGORIES).optional(),
    parent: z.string().optional(),
    occupants: z.array(z.string()).default([]),
    nearby: z.array(z.string()).default([]),
    plaque: z.string().optional(),
    couplet: z
      .object({
        upper: z.string(),
        lower: z.string(),
      })
      .optional(),
    features: z.array(z.string()).default([]),
    furnishings: z.array(z.string()).default([]),
    plants: z.array(z.string()).default([]),
    first_appear: z.string().optional(),
    appear_in: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    // 取经路线 GIS（西游记专用，可选）
    realm: z.string().optional(),
    layer: z.enum(ROUTE_LAYERS).optional(),
    coord: z.object({ x: z.number(), y: z.number() }).optional(),
    route_order: z.number().optional(),
  }),
});

const medicines = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/medicines' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['medicine', 'prescription', 'diagnosis']),
    name: z.string(),
    book: z.enum(BOOKS),
    category: z.string().optional(),
    patient: z.string().optional(),
    prescriber: z.string().optional(),
    physician: z.string().optional(),
    ingredients: z.array(z.string()).default([]),
    process: z.string().optional(),
    syndrome: z.string().optional(),
    pulse: z.string().optional(),
    effect_literary: z.string().optional(),
    effect_scholarly: z.string().optional(),
    first_appear: z.string().optional(),
    appear_in: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
  }),
});

const dishes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/dishes' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['dish', 'banquet', 'tea', 'wine', 'ingredient']),
    name: z.string(),
    book: z.enum(BOOKS),
    category: z.string().optional(),
    ingredients: z.array(z.string()).default([]),
    process: z.string().optional(),
    cost_estimate: z.string().optional(),
    temperature: z.string().optional(),
    eaters: z.array(z.string()).default([]),
    location: z.string().optional(),
    occasion: z.string().optional(),
    literary_vs_real: z.enum(['literary', 'plausible_qing', 'disputed']).optional(),
    first_appear: z.string().optional(),
    appear_in: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
  }),
});

const costumes = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/costumes' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['costume', 'accessory', 'fabric']),
    name: z.string(),
    book: z.enum(BOOKS),
    wearer: z.string().optional(),
    material: z.string().optional(),
    color: z.string().optional(),
    occasion: z.string().optional(),
    rank_signal: z.string().optional(),
    first_appear: z.string().optional(),
    appear_in: z.array(z.string()).default([]),
    description: z.string().optional(),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
  }),
});

const customs = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/customs' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['festival', 'wedding', 'funeral', 'ritual', 'institution', 'currency']),
    name: z.string(),
    book: z.enum(BOOKS),
    participants: z.array(z.string()).default([]),
    procedure: z.array(z.string()).default([]),
    location: z.string().optional(),
    economic: z.string().optional(),
    legal_norm: z.string().optional(),
    first_appear: z.string().optional(),
    appear_in: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
  }),
});

const IMAGERY_PREDICATES = [
  '对应判词', '作', '吟', '隐喻', '影射', '象征', '预示', '互文',
] as const;

const imageryLink = z.object({
  target: z.string(),
  target_kind: z.enum(['character', 'imagery']).default('character'),
  predicate: z.enum(IMAGERY_PREDICATES),
  inference: z.boolean().default(false),
  chapter: z.number().optional(),
  source: z.string().optional(),
  note: z.string().optional(),
});

const IMAGERY_SUBTYPES = ['judgment', 'poem', 'symbol', 'flower_lot'] as const;

const imagery = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/imagery' }),
  schema: z.object({
    id: z.string(),
    type: z.literal('imagery'),
    book: z.enum(BOOKS),
    subtype: z.enum(IMAGERY_SUBTYPES),
    title: z.string(),
    text: z.string().optional(),
    chapters: z.array(z.number()).default([]),
    characters: z.array(z.string()).default([]),
    links: z.array(imageryLink).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    source: z.string().optional(),
  }),
});

const EVENT_SUBTYPES = ['tribulation', 'plot'] as const;

const scopedRelation = z.object({
  subject: z.string(),
  predicate: z.string(),
  object: z.string(),
  chapter: z.number().optional(),
  source: z.string().optional(),
  ephemeral: z.boolean().optional(),
});

const events = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/events' }),
  schema: z.object({
    id: z.string(),
    type: z.literal('event'),
    book: z.enum(BOOKS),
    subtype: z.enum(EVENT_SUBTYPES).default('tribulation'),
    tribulation_no: z.number().optional(),
    title: z.string(),
    aliases: z.array(z.string()).default([]),
    chapters: z.array(z.number()).default([]),
    locations: z.array(z.string()).default([]),
    characters: z.array(z.string()).default([]),
    monsters: z.array(z.string()).default([]),
    artifacts: z.array(z.string()).default([]),
    prev: z.string().optional(),
    next: z.string().optional(),
    scoped_relations: z.array(scopedRelation).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    source: z.string().optional(),
  }),
});

const TRANSACTION_SUBTYPES = [
  '奴婢买卖', '贿赂', '借贷', '买卖', '馈赠', '经营投资',
  '酒席宴请', '宗教布施', '帮闲', '赎当', '财礼', '收礼', '其他',
] as const;

const CURRENCY_UNITS = ['银', '钱', '贯', '文'] as const;

const transactions = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/transactions' }),
  schema: z.object({
    id: z.string(),
    type: z.literal('transaction'),
    book: z.enum(BOOKS),
    subtype: z.enum(TRANSACTION_SUBTYPES),
    amount: z.number(),
    currency: z.enum(CURRENCY_UNITS),
    amount_normalized: z.number().optional(),
    conversion_note: z.string().optional(),
    conversion_disputed: z.boolean().optional(),
    buyer: z.string().optional(),
    seller: z.string().optional(),
    payee: z.string().optional(),
    item_ref: z.string().optional(),
    pool_from: z.string(),
    pool_to: z.string(),
    chapter: z.number(),
    source: z.string().optional(),
    edition: z.string().optional(),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
  }),
});

export const collections = {
  characters,
  chapters,
  books,
  locations,
  medicines,
  dishes,
  costumes,
  customs,
  transactions,
  events,
  imagery,
};
