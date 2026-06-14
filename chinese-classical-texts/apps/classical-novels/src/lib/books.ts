export type ThemeKey = 'honglou' | 'xiyouji' | 'jinpingmei';

export interface ModulePreview {
  intro: string;
  dimensions: { title: string; desc: string }[];
  phases: string[];
  relatedDoc: string;
}

export interface BookModule {
  key: string;
  glyph: string;
  title: string;
  desc: string;
  href?: string;
  status: 'live' | 'planned';
  preview?: ModulePreview;
}

export interface BookTheme {
  theme: ThemeKey;
  essence: string;
  tagline: string;
  motifs: string[];
}

export const THEME_BY_SLUG: Record<string, BookTheme> = {
  honglou: {
    theme: 'honglou',
    essence: '一首没落贵族的挽歌',
    tagline: '钟鸣鼎食 · 终成虚话',
    motifs: ['绛珠还泪', '通灵宝玉', '大观园'],
  },
  xiyouji: {
    theme: 'xiyouji',
    essence: '一场浪漫的神魔修心之旅',
    tagline: '九九八十一难 · 明心见性',
    motifs: ['金箍棒', '八十一难', '取经路'],
  },
  jinpingmei: {
    theme: 'jinpingmei',
    essence: '一面照见晚明世情的照妖镜',
    tagline: '金银满箧 · 终归一梦',
    motifs: ['白银流转', '西门府', '市井百态'],
  },
};

export function themeFor(slug: string | undefined): ThemeKey | undefined {
  return slug ? THEME_BY_SLUG[slug]?.theme : undefined;
}

function live(ok: boolean, slug: string, key: string, real: string): Pick<BookModule, 'status' | 'href'> {
  return ok ? { status: 'live', href: real } : { status: 'planned', href: `/${slug}/m/${key}` };
}

function plan(slug: string, key: string): Pick<BookModule, 'status' | 'href'> {
  return { status: 'planned', href: `/${slug}/m/${key}` };
}

/**
 * 各书功能模块清单（依据 docs 学术映射）。
 * - core 模块按 features 开关决定 live/planned，并指向真实页面
 * - 未做模块固定 planned，并指向「模块预览页」/[book]/m/[key]（UI 标「未做」）
 */
export function modulesFor(slug: string, features: string[]): BookModule[] {
  const has = (f: string) => features.includes(f);
  switch (slug) {
    case 'honglou':
      return [
        { key: 'read', glyph: '读', title: '逐回精读', desc: '脂本优先 · 程高本续书', status: 'live', href: `/${slug}/read/zhiben` },
        { key: 'graph', glyph: '谱', title: '人物关系', desc: '四大家族 · 主仆 · 情感盟约', ...live(has('graph'), slug, 'graph', `/${slug}/graph`) },
        { key: 'bestiary', glyph: '鉴', title: '人物图鉴', desc: '金陵十二钗与丫鬟群像', ...live(has('bestiary'), slug, 'bestiary', `/${slug}/bestiary`) },
        { key: 'places', glyph: '园', title: '大观园', desc: '院落居所 · 匾额对联 · 居住分派', ...live(has('places'), slug, 'places', `/${slug}/places`) },
        { key: 'items', glyph: '物', title: '名物百科', desc: '饮食 · 医药 · 服饰纵切研究', ...live(has('items'), slug, 'items', `/${slug}/items`) },
        {
          key: 'shi', glyph: '诗', title: '诗词意象', desc: '葬花吟 · 判词 · 花签隐喻', ...live(has('poems'), slug, 'shi', `/${slug}/shi`),
          preview: {
            intro:
              '《红楼梦》以「图谶式」笔法把人物结局藏进名字、诗词与器物。本模块把表层意象与其隐喻的人物命运关联起来，是区别于普通小说图谱的高阶文学维度。',
            dimensions: [
              { title: '判词曲子', desc: '太虚幻境十二钗判词与《红楼梦曲》→ 预示各人结局' },
              { title: '诗社作品', desc: '海棠诗、菊花诗、《葬花吟》→ 性格与命运的投射' },
              { title: '花签酒令', desc: '群芳夜宴花名签 → 黛玉芙蓉、宝钗牡丹的隐喻' },
              { title: '象征物互文', desc: '玉 / 金 / 竹 / 芙蓉 的意象网络（晴为黛影）' },
            ],
            phases: [
              'P1 录入判词与对应人物的「隐喻」推论边（标注 inference，可溯源）',
              'P2 诗词意象 × 章回 × 人物交叉索引',
              'P3 意象互文网络可视化（如 晴雯—芙蓉—黛玉 链路）',
            ],
            relatedDoc: '红楼梦-知识图谱架构.md（文本意象与互文网络维度）',
          },
        },
        kaozhengModule(slug, has),
      ];
    case 'xiyouji':
      return [
        { key: 'read', glyph: '读', title: '逐回精读', desc: '100 回世德堂本', status: 'live', href: `/${slug}/read/1` },
        { key: 'graph', glyph: '谱', title: '取经关系', desc: '师徒 · 神魔 · 降服与求援', ...live(has('graph'), slug, 'graph', `/${slug}/graph`) },
        { key: 'bestiary', glyph: '妖', title: '妖怪图鉴', desc: '本相 · 靠山 · 结局（背景论）', ...live(has('bestiary'), slug, 'bestiary', `/${slug}/bestiary`) },
        { key: 'items', glyph: '宝', title: '法宝谱系', desc: '制造 · 拥有 · 克制关系', ...live(has('items'), slug, 'items', `/${slug}/items`) },
        {
          key: 'nan', glyph: '难', title: '八十一难', desc: '劫难单元时间轴', ...live(has('nan'), slug, 'nan', `/${slug}/nan`),
          preview: {
            intro:
              '取经历程由「九九八十一难」单元串成。本模块以劫难为线索，组织事件、妖魔、地点、法宝，并按前后置顺序还原完整西行时间轴。',
            dimensions: [
              { title: '劫难单元', desc: '标准化难目（三打白骨精、三调芭蕉扇…）与对应回目' },
              { title: '妖魔靠山', desc: '每难妖魔的本相 / 后台 / 结局（有背景 vs 无背景）' },
              { title: '法宝克制', desc: '难中关键法宝与克制关系（如定风丹克芭蕉扇）' },
              { title: '前后置顺序', desc: '劫难顺序边，串出完整西行时间轴' },
            ],
            phases: [
              'X1 建 event 实体与回目锚点',
              'X2 难—妖—宝—地 四元关联',
              'X3 时间轴可视化 + 靠山/难度统计',
            ],
            relatedDoc: '西游记-知识图谱架构.md（劫难 / 事件层）',
          },
        },
        {
          key: 'route', glyph: '图', title: '取经路线', desc: '真实地理 + 神话地理双层 GIS', ...live(has('route'), slug, 'route', `/${slug}/route`),
          preview: {
            intro:
              '西行空间是「双层地理」：真实地理（长安→天竺）叠加神话地理（天界 / 幽冥 / 洞府）。本模块把每难的发生地落到地图，支持双层切换。',
            dimensions: [
              { title: '凡间路线', desc: '长安、五行山、火焰山、车迟国… 途经国度' },
              { title: '神话坐标', desc: '天宫、灵山、地府、龙宫等异界' },
              { title: '事件落点', desc: '每难发生地与 location 实体绑定' },
              { title: '双层叠加', desc: '真实 / 神话地理图层切换渲染' },
            ],
            phases: [
              'X1 location 实体补全（含异界坐标）',
              'X2 事件 — 地点绑定',
              'X3 GIS 双层地图渲染',
            ],
            relatedDoc: '西游记-知识图谱架构.md（地理坐标层）',
          },
        },
        {
          key: 'quanshi', glyph: '诠', title: '诠释专题', desc: '内丹心性 · 政治隐喻 · 原型源流',
          ...live(has('quanshi'), slug, 'quanshi', `/${slug}/quanshi`),
          preview: {
            intro:
              '《西游记》自明清以来被反复「诠释」：道家读作内丹修炼，士人读作官场讽喻，学者考其原型源流。本模块把这些读法作为分层的「诠释」（inference）沉淀，并叠加「情境边」——变身/伪装等临时关系。',
            dimensions: [
              { title: '内丹心性', desc: '心猿意马、金公木母；刘一明《西游原旨》等丹道解' },
              { title: '政治隐喻', desc: '天庭官僚、有无背景的妖怪、对明代政治的讽喻' },
              { title: '原型源流', desc: '孙悟空（无支祁/哈奴曼之争）、唐僧=玄奘历史原型' },
              { title: '情境边', desc: '变身/伪装等 ephemeral 关系（六耳猕猴假冒、白骨精三变）' },
            ],
            phases: [
              'X4 symbol + inference 边录入（标注 inference，可溯源）',
              'X4 情境边（scoped_relations）叠加到事件与图谱',
              'X4 刘一明等诠释专题 topic',
            ],
            relatedDoc: '西游学分支与产品映射.md（⑤ 诠释 + 情境边）',
          },
        },
        kaozhengModule(slug, has),
      ];
    case 'jinpingmei':
      return [
        { key: 'read', glyph: '读', title: '逐回精读', desc: '词话 · 崇祯 · 竹坡三版本', status: 'live', href: `/${slug}/read/cihua` },
        { key: 'graph', glyph: '谱', title: '西门府社会网', desc: '妻妾 · 帮闲 · 政商利益', ...live(has('graph'), slug, 'graph', `/${slug}/graph`) },
        { key: 'bestiary', glyph: '鉴', title: '人物图鉴', desc: '妻妾 · 帮闲 · 政商群像', ...live(has('bestiary'), slug, 'bestiary', `/${slug}/bestiary`) },
        { key: 'places', glyph: '府', title: '西门府', desc: '院落居所 · 店铺 · 县城市井', ...live(has('places'), slug, 'places', `/${slug}/places`) },
        {
          key: 'chain', glyph: '链', title: '发家衰败链', desc: '白银节点 · 情节转折 · 回目时间轴', ...live(has('chain'), slug, 'chain', `/${slug}/chain`),
          preview: {
            intro:
              '以 event 实体串联西门府从药铺发迹、政商攀升到暴亡散府的完整脉络，白银节点与情节节点前后置链接，可与白银流模块互证。',
            dimensions: [
              { title: '白银节点', desc: 'financial_event：药铺、放债、贿赂、遗产等' },
              { title: '情节节点', desc: 'plot：得官、丧礼、暴亡、散府' },
              { title: '前后置链', desc: 'prev/next 边，按回目排序渲染时间轴' },
              { title: '四阶段', desc: '发家根基 → 政商攀升 → 鼎盛极奢 → 衰败散府' },
            ],
            phases: [
              'P2 chain 时间轴 UI（本页）',
              'P3 增补 event + transaction_refs 自动链接',
              'P4 与 SNA / 白银桑基图联动高亮',
            ],
            relatedDoc: '金瓶梅.log.md · events/金瓶梅/',
          },
        },
        {
          key: 'silver', glyph: '银', title: '物价 · 白银流', desc: '交易记录 · 银两换算 · 资金流向', ...live(has('silver'), slug, 'silver', `/${slug}/silver`),
          preview: {
            intro:
              '《金瓶梅》对金钱描写精准到令人发指。本模块以「物质·金钱」为纬，记录每笔交易并把货币标准化为「两银」，可视化西门府的白银流向。',
            dimensions: [
              { title: '交易记录', desc: 'transaction 实体：标的 / 金额 / 来源 / 流向' },
              { title: '货币换算', desc: '银·钱·贯·文 → 统一「两银」，保留可溯源换算链' },
              { title: '资金池', desc: '放贷 / 送礼 / 经营三条白银流入流出' },
              { title: '物价对勘', desc: '同一物价在词话本 / 崇祯本的异文变动' },
            ],
            phases: [
              'J1 transaction / financial_event schema 落地',
              'J2 /ingest 货币换算标准化（amount_normalized）',
              'J3 白银流向桑基图 / 资金池可视化',
            ],
            relatedDoc: '金瓶梅-知识图谱架构.md（§四–§六）',
          },
        },
        {
          key: 'material', glyph: '物', title: '物质百科', desc: '服饰 · 饮食 · 药材', ...live(has('items'), slug, 'material', `/${slug}/items`),
          preview: {
            intro:
              '提取《金瓶梅》的物质实体，会得到一部庞大的晚明生活百科——服饰、饮食、药材皆有极专业的描写，可作社会人类学切片。',
            dimensions: [
              { title: '服饰', desc: '材质 / 颜色 / 形制（如大红刻丝段子对衿圆领）' },
              { title: '饮食', desc: '珍馐做法、酒类、宴席成本' },
              { title: '药材', desc: '方剂、春药与晚明纵欲心理' },
              { title: '占有关系', desc: '物品与人物的持有 / 赠予链' },
            ],
            phases: [
              'J1 开启 items（dish / costume / medicine）feature',
              'J2 物 — 人 — 地 交叉索引',
              'J3 物质消费与身份 / 经济关联分析',
            ],
            relatedDoc: '金瓶梅-知识图谱架构.md（物质与商品层）',
          },
        },
        {
          key: 'edition', glyph: '勘', title: '版本对勘', desc: '词话本 vs 崇祯本异文', ...live(has('compare'), slug, 'edition', `/${slug}/compare`),
          preview: {
            intro:
              '《金瓶梅》是部禁书，在地下秘密流传中被不断修改。本模块对勘三大版本系统的异文，追踪情节的删减与润色。',
            dimensions: [
              { title: '三大版本', desc: '词话本（说书痕迹）/ 崇祯本（文人润色）/ 张竹坡评本' },
              { title: '异文锚点', desc: '同一事件在不同版本的表述差异' },
              { title: '物价变动', desc: '某处物价在版本间是否改动' },
              { title: '删润标注', desc: '情节被删减还是润色，逐处标记' },
            ],
            phases: [
              'J1 chapter.edition 多版本并存',
              'J2 variants 异文标注（schema 已就绪）',
              'J3 双栏对勘视图',
            ],
            relatedDoc: '金学分支与产品映射.md · 金瓶梅-知识图谱架构.md',
          },
        },
        {
          key: 'sna', glyph: '网', title: '社会网络分析', desc: '帮闲圈介数中心性 SNA', ...live(has('sna'), slug, 'sna', `/${slug}/sna`),
          preview: {
            intro:
              '把西门府的人际勾连作为社会网络，用图算法找出把控信息与利益流动的关键掮客——这是《金瓶梅》作为「社会人类学报告」的核心价值。',
            dimensions: [
              { title: '多类型关系网', desc: '妻妾 / 帮闲 / 政商 / 仆佣 多类型边' },
              { title: '介数中心性', desc: '定位「核心帮闲圈」关键节点（如应伯爵）' },
              { title: '利益距离', desc: '每人与西门府的亲缘 / 雇佣 / 利益交换距离' },
              { title: '派系社群', desc: '社群发现划分府内派系' },
            ],
            phases: [
              'J1 关系受控词表扩展（贿赂 / 帮闲 / 借贷 / 认干亲…）',
              'J2 SNA 指标计算（介数 / 度中心性）',
              'J3 中心性叠加到关系图谱',
            ],
            relatedDoc: '金瓶梅-知识图谱架构.md（§五 SNA）',
          },
        },
        kaozhengModule(slug, has),
      ];
    default:
      return [];
  }
}

/** 考证台模块（三书共用）：成书史 / 版本学 / 作者公案 / 假说卡（inference 分层） */
function kaozhengModule(slug: string, has: (f: string) => boolean): BookModule {
  const descBySlug: Record<string, string> = {
    honglou: '版本（脂/程）· 曹家成书 · 探佚公案',
    jinpingmei: '三版本对勘 · 兰陵笑笑生公案',
    xiyouji: '世德堂成书 · 吴承恩/丘处机公案',
  };
  return {
    key: 'kaozheng',
    glyph: '考',
    title: '考证台',
    desc: descBySlug[slug] ?? '成书史 · 版本学 · 作者公案',
    ...live(has('kaozheng'), slug, 'kaozheng', `/${slug}/kaozheng`),
    preview: {
      intro:
        '考证台汇集一部书的「身世之谜」：成书源流、版本系统、作者公案。所有作者归属、探佚结论一律作为分层的「假说卡」（inference）呈现，挂证据链，绝不写成事实。',
      dimensions: [
        { title: '成书史', desc: '从素材到定本的演化（增删、话本、对勘）' },
        { title: '版本学', desc: '版本系统与异文（脂/程、词话/崇祯/竹坡、世德堂…）' },
        { title: '作者公案', desc: '作者归属诸说，逐条标可信度与证据' },
        { title: '假说卡', desc: 'inference 分层：主流 / 存疑 / 少数 / 已弃' },
      ],
      phases: [
        '成书史 / 版本学 / 作者公案 topic 落地',
        '假说卡（hypotheses）录入，标注 stance 与证据',
        '与版本对勘 / 探佚图谱矛盾边互链',
      ],
      relatedDoc: '红学/西游学/金学 分支与产品映射.md（考证台）',
    },
  };
}
