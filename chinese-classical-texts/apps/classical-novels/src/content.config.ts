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

// 人物路线图 · 一生轨迹节点（出身→转折→结局）。fortune 为命运值（-100 低谷 ~ 100 高光），驱动命运曲线
export const ARC_STAGES = ['出场', '起', '转', '高光', '低谷', '结局'] as const;

const characterArc = z.object({
  chapter: z.number().optional(),
  stage: z.enum(ARC_STAGES).optional(),
  title: z.string(),
  note: z.string().optional(),
  fortune: z.number().min(-100).max(100).optional(),
  event: z.string().optional(),
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
    // 金瓶梅 · 图鉴扩展（P5）
    靠山: z.string().optional(),
    依附: z.string().optional(),
    // 红楼梦 · 图鉴扩展
    性格: z.string().optional(),
    喜好: z.array(z.string()).default([]),
    服饰: z.array(z.string()).default([]),
    关键物品: z.array(z.string()).default([]),
    // 关系与版本
    relations: z.array(relation).default([]),
    variants: z.array(variant).default([]),
    contradicts: z.array(z.string()).default([]),
    // 人物路线图 · 一生轨迹（可选，仅录入主角；空则不显示路线页）
    arc: z.array(characterArc).default([]),
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
      z.enum(['reader', 'graph', 'bestiary', 'items', 'poems', 'places', 'silver', 'sna', 'compare', 'nan', 'route', 'chain', 'town', 'garden', 'manor', 'scene', 'kaozheng', 'quanshi', 'saga'])
    ),
    summary: z.string().optional(),
  }),
});

const LOCATION_CATEGORIES = [
  '府邸', '花园', '院落', '亭', '楼', '阁', '榭', '堂', '馆', '庵', '祠', '闸', '桥', '幻境', '市街',
  '衙署',
  '道院',
  // 金瓶梅 · 市井地理
  '街巷', '府治', '县治', '关津', '津渡', '河岸', '庄园', '园林', '宅', '寺',
  // 西游记 · 取经地理
  '国度', '山岭', '洞府', '水域', '天界', '地府', '仙山', '城关', '寺观',
  '其他',
] as const;

// 西游记取经路线 GIS：地理分层（real 凡间路线 / myth 神话异界）
const ROUTE_LAYERS = ['real', 'myth'] as const;

// 红楼梦大观园地图分区
const GARDEN_ZONES = ['居所', '水系', '仪典', '路径', '亭榭', '寺观', '服务'] as const;
const MANOR_ZONES = ['荣府轴', '荣府侧', '宁府轴', '宁府园', '连接', '外联'] as const;

const locations = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/locations' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['location', 'building', 'garden', 'temple', 'realm']),
    name: z.string(),
    aliases: z.array(z.string()).default([]),
    book: z.enum(BOOKS),
    category: z.enum(LOCATION_CATEGORIES).optional(),
    parent: z.string().nullish(),
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
    map_zone: z.enum(['府内', '市井', '寺观', '城外']).optional(),
    garden_zone: z.enum(GARDEN_ZONES).optional(),
    manor_zone: z.enum(MANOR_ZONES).optional(),
    tour_order: z.number().optional(),
    // 取经路线 GIS（西游记专用，可选）
    realm: z.string().optional(),
    layer: z.enum(ROUTE_LAYERS).optional(),
    coord: z.object({ x: z.number(), y: z.number() }).optional(),
    /** 真实经纬度（取经路线方位投影用） */
    geo: z.object({ lat: z.number(), lng: z.number() }).optional(),
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

const ARTIFACT_RELATION_TYPES = ['制造', '拥有', '克制', '赠与', '盗取'] as const;

const artifactRelation = z.object({
  target: z.string(),
  type: z.enum(ARTIFACT_RELATION_TYPES),
  note: z.string().optional(),
});

const artifacts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/artifacts' }),
  schema: z.object({
    id: z.string(),
    type: z.enum(['weapon', 'container', 'talisman', 'implement']),
    name: z.string(),
    book: z.enum(BOOKS),
    category: z.string().optional(),
    maker: z.string().optional(),
    owner: z.string().optional(),
    weight: z.string().optional(),
    abilities: z.array(z.string()).default([]),
    counters: z.array(z.string()).default([]),
    relations: z.array(artifactRelation).default([]),
    first_appear: z.string().optional(),
    appear_in: z.array(z.string()).default([]),
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
  // 红楼 · 双层镜像（太虚↔人间）映射边 + 影身边
  '还泪', '历劫', '投影', '归彼大荒', '影身',
  // 金瓶 · 名字谶 / 物象流转 / 因果反噬
  '谐音', '流转', '反噬', '催命',
  // 西游 · 五行生克（丹道）
  '相克', '交并', '调和', '相济',
] as const;

// 金瓶 · 因果报应闭环：欲起→聚敛→极盛→反噬→散尽（以李瓶儿之死为冷热转折）
const IMAGERY_PHASES = ['欲起', '聚敛', '极盛', '反噬', '散尽'] as const;

const imageryLink = z.object({
  target: z.string(),
  target_kind: z.enum(['character', 'imagery']).default('character'),
  predicate: z.enum(IMAGERY_PREDICATES),
  inference: z.boolean().default(false),
  chapter: z.number().optional(),
  source: z.string().optional(),
  note: z.string().optional(),
  // 金瓶 · 时序闭环：阶段 + 冷热（张竹坡「冷热金针」）
  phase: z.enum(IMAGERY_PHASES).optional(),
  temperature: z.enum(['冷', '热']).optional(),
});

const IMAGERY_SUBTYPES = [
  'judgment', 'poem', 'symbol', 'flower_lot', 'myth',
  // 金瓶 · 世情物语
  'name_omen', 'object_omen', 'tune_omen',
  // 西游 · 丹道意象
  'alchemy', 'place_omen',
] as const;

const imagery = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/imagery' }),
  schema: z.object({
    id: z.string(),
    type: z.literal('imagery'),
    book: z.enum(BOOKS),
    subtype: z.enum(IMAGERY_SUBTYPES),
    title: z.string(),
    text: z.string().optional(),
    // 红楼 · 双层镜像：太虚幻境（神话层）/ 人间贾府（现实层）
    layer: z.enum(['太虚', '人间']).optional(),
    chapters: z.array(z.number()).default([]),
    characters: z.array(z.string()).default([]),
    links: z.array(imageryLink).default([]),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    source: z.string().optional(),
  }),
});

const EVENT_SUBTYPES = ['tribulation', 'plot', 'financial', 'milestone'] as const;

const FINANCIAL_KINDS = ['药铺', '放债', '贿赂', '遗产', '经营', '买卖'] as const;

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
    // 红楼梦 · 大事记版本归属（曹著/脂本 vs 程高本补）
    edition: z.string().optional(),
    // 金瓶梅 · 经济事件
    financial_kind: z.enum(FINANCIAL_KINDS).optional(),
    amount_liang: z.number().optional(),
    transaction_refs: z.array(z.string()).default([]),
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
    // 红楼梦 · 版本异文（脂本探佚 vs 程高本续补）与矛盾主题标记
    variants: z.array(variant).default([]),
    contradicts: z.array(z.string()).default([]),
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

const VARIANT_CATEGORIES = ['回目', '删润', '物价', '措辞', '情节', '批语'] as const;

const textVariants = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/variants' }),
  schema: z.object({
    id: z.string(),
    type: z.literal('variant'),
    book: z.enum(BOOKS),
    chapter: z.number(),
    category: z.enum(VARIANT_CATEGORIES),
    edition_a: z.string(),
    edition_b: z.string(),
    text_a: z.string().optional(),
    text_b: z.string().optional(),
    note: z.string().optional(),
    tags: z.array(z.string()).default([]),
    summary: z.string(),
    topic_id: z.string().optional(),
  }),
});

// 主题页 / 回填产物（/query、考证台、诠释专题）
const TOPIC_TYPES = ['topic', '对比', '分析'] as const;
// 模块归属：综述（默认）/ 考证（成书史·版本学·作者公案）/ 诠释（内丹·政治·原型…）
const TOPIC_CATEGORIES = ['综述', '考证', '诠释'] as const;
// 考证台分支
const KAOZHENG_BRANCHES = ['成书史', '版本学', '作者公案'] as const;
// 诠释视角（西游记为主）
const QUANSHI_LENSES = ['内丹', '政治', '原型', '民俗', '叙事', '宗教'] as const;
// 假说可信度分层（事实 → 推论分级；作者归属等一律标推论）
const HYPOTHESIS_STANCES = ['主流', '存疑', '少数', '已弃'] as const;

// 假说卡（作者公案 / 探佚等），inference 分层的核心载体
const hypothesis = z.object({
  claim: z.string(),
  proponent: z.string().optional(),
  period: z.string().optional(),
  stance: z.enum(HYPOTHESIS_STANCES).default('存疑'),
  evidence: z.array(z.string()).default([]),
  counter: z.string().optional(),
  source: z.string().optional(),
});

// 诠释条目（符号 → 义理），默认 inference: true
const reading = z.object({
  lens: z.enum(QUANSHI_LENSES),
  symbol: z.string(),
  meaning: z.string(),
  proponent: z.string().optional(),
  inference: z.boolean().default(true),
  source: z.string().optional(),
});

const topics = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/topics' }),
  schema: z.object({
    type: z.enum(TOPIC_TYPES).default('topic'),
    book: z.enum(BOOKS),
    title: z.string(),
    category: z.enum(TOPIC_CATEGORIES).default('综述'),
    branch: z.enum(KAOZHENG_BRANCHES).optional(),
    lens: z.enum(QUANSHI_LENSES).optional(),
    derived_from: z.array(z.string()).default([]),
    created: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    summary: z.string().optional(),
    hypotheses: z.array(hypothesis).default([]),
    readings: z.array(reading).default([]),
  }),
});

export const collections = {
  characters,
  chapters,
  books,
  topics,
  locations,
  artifacts,
  medicines,
  dishes,
  costumes,
  customs,
  transactions,
  events,
  variants: textVariants,
  imagery,
};
