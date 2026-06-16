import { moduleCopy } from './module-copy';
import type { BookSlug, SiteLocale } from './types';

const bookMeta = {
  honglou: {
    tagline: { zh: '钟鸣鼎食 · 终成虚话', en: 'Bells & tripods · all turns to void', ja: '鐘鳴鼎食 · 終に虚話' },
    editionNote: {
      zh: ' · 脂本优先 · 程高本续书',
      en: ' · Zhiping first · Chen-Gao continuation',
      ja: ' · 脂本優先 · 程高本続編',
    },
  },
  jinpingmei: {
    tagline: { zh: '金银满箧 · 终归一梦', en: 'Gold & silver fill the chest · one dream in the end', ja: '金銀満箧 · 結局は一夢' },
    editionNote: {
      zh: ' · 词话本优先 · 三版本',
      en: ' · Cihua first · three editions',
      ja: ' · 詞話本優先 · 三版本',
    },
  },
  xiyouji: {
    tagline: { zh: '九九八十一难 · 明心见性', en: 'Eighty-one trials · see your true mind', ja: '九九八十一難 · 明心見性' },
    editionNote: { zh: '', en: '', ja: '' },
  },
} as const;

function booksFor(locale: SiteLocale) {
  const home = {
    zh: {
      honglou: {
        essence: '一首没落贵族的挽歌',
        summary: '以贾府兴衰与宝黛爱情为主线的章回体长篇小说，存脂评本与程高本异文。',
        motifs: ['绛珠还泪', '通灵宝玉', '大观园'],
      },
      xiyouji: {
        essence: '一场浪漫的神魔修心之旅',
        summary: '唐僧师徒西天取经，八十一难历劫修心，神魔与人性并写的长篇神魔小说。',
        motifs: ['金箍棒', '八十一难', '取经路'],
      },
      jinpingmei: {
        essence: '一面照见晚明世情的照妖镜',
        summary: '以西门庆家族与市井网络写晚明世态，金银、欲望与衰败交织的长篇章回小说。',
        motifs: ['白银流转', '西门府', '市井百态'],
      },
    },
    en: {
      honglou: {
        essence: 'An elegy for a declining aristocratic house',
        summary:
          'A chapter novel centered on the Jia clan’s rise and fall and the Ba–Dai bond, with Zhiping and Chen-Gao textual variants.',
        motifs: ['Crimson Pearl’s tears', 'Magic Jade', 'Grand View Garden'],
      },
      xiyouji: {
        essence: 'A romantic journey of gods, demons, and self-cultivation',
        summary:
          'Tripitaka’s pilgrimage westward through eighty-one tribulations—a long religious fantasy of trial and awakening.',
        motifs: ['Iron Staff', '81 tribulations', 'The road west'],
      },
      jinpingmei: {
        essence: 'A mirror held up to late-Ming society',
        summary:
          'The Ximen household and urban networks expose desire, silver, and decay in a full-length worldly novel.',
        motifs: ['Silver in motion', 'Ximen mansion', 'Street life'],
      },
    },
    ja: {
      honglou: {
        essence: '没落する貴族の挽歌',
        summary: '賈府の興亡と宝黛の恋を軸とする章回小説。脂評本と程高本の異文を収録。',
        motifs: ['絳珠返涙', '通霊宝玉', '大観園'],
      },
      xiyouji: {
        essence: '神魔と修心のロマンな旅',
        summary: '唐僧一行の西天取经、八十一難を経た修行の長編神魔小説。',
        motifs: ['金箍棒', '八十一難', '取经路'],
      },
      jinpingmei: {
        essence: '晚明の世相を映す鏡',
        summary: '西门庆家と市井のネットワークで欲望・銀・衰败を描く長篇章回小説。',
        motifs: ['白銀の流れ', '西門府', '市井百態'],
      },
    },
  }[locale];

  return (['honglou', 'xiyouji', 'jinpingmei'] as BookSlug[]).reduce(
    (acc, slug) => {
      acc[slug] = {
        ...home[slug],
        tagline: bookMeta[slug].tagline[locale],
        editionNote: bookMeta[slug].editionNote[locale],
      };
      return acc;
    },
    {} as Record<
      BookSlug,
      {
        essence: string;
        summary: string;
        motifs: string[];
        tagline: string;
        editionNote: string;
      }
    >,
  );
}

export const messages = {
  zh: {
    siteTitle: '古典名著知识库',
    search: '检索',
    pageTitle: '首页',
    subtitle: '中 国 古 典 名 著 · 知 识 图 谱',
    title: '三大奇书',
    lead1: '以 raw 只读真相源为根，LLM 维护的人物、关系、名物与版本图谱。',
    lead2: '一部贵族挽歌，一程神魔修心，一面世情照妖镜。',
    booksMissingTitle: '书目卡片未加载',
    booksMissingBody:
      '开发模式下 Astro 内容库写入失败（常见于 Windows 上多个 dev 进程争用 .astro/data-store.json）。请在项目目录执行 npm run dev:clean，只保留一个 dev 实例；或使用 npm run build && npm run preview。',
    enter: '入 →',
    footer: '数据由 LLM 按 AGENTS.md 维护 · 原文只读真相源 · 事实与推论分层',
    chapterUnit: '回',
    nav: { canon: '典籍', search: '检索', modules: '探索模块' },
    ui: {
      exploreModules: '探索模块',
      chapterIndex: '回目目录',
      fullTextSearch: '全文检索',
      planned: '未做',
      searchTitle: '站内检索',
      searchLead: '检索范围：已 ingest 的回目、人物 / 妖怪、主题页。原文随导入逐步纳入。',
      contentNote: '条目正文与章回原文保持中文；切换语言仅影响界面导航与模块说明。',
      itemsFoldHint: '分类已折叠 — 点击「全部展开」查看名物卡片',
      itemsEmpty: '本书暂无名物实体页。',
      itemsExtraPrefix: '医药、饮食、服饰、民俗规章实体（共',
      itemsExtraSuffix: '条）',
      kaozhengEmpty: '尚无考证专题。请在 src/content/topics/ 下新建 category: 考证 的 topic。',
    },
    books: booksFor('zh'),
    modules: moduleCopy.zh,
  },
  en: {
    siteTitle: 'Classical Novels Wiki',
    search: 'Search',
    pageTitle: 'Home',
    subtitle: 'C L A S S I C A L · N O V E L S · K N O W L E D G E · G R A P H',
    title: 'Three Masterworks',
    lead1: 'Built on read-only source texts, with LLM-curated characters, relations, artifacts, and edition graphs.',
    lead2: 'An aristocratic elegy, a spiritual pilgrimage, and a mirror of late-Ming worldly life.',
    booksMissingTitle: 'Book cards failed to load',
    booksMissingBody:
      'Content collection sync failed in dev (often multiple dev processes on Windows). Run npm run dev:clean and keep one dev server, or npm run build && npm run preview.',
    enter: 'Enter →',
    footer: 'Curated by LLM per AGENTS.md · Read-only sources · Facts separated from inference',
    chapterUnit: 'ch.',
    nav: { canon: 'Canon', search: 'Search', modules: 'Modules' },
    ui: {
      exploreModules: 'Explore modules',
      chapterIndex: 'Chapter index',
      fullTextSearch: 'Full-text search',
      planned: 'Planned',
      searchTitle: 'Site search',
      searchLead: 'Search ingested chapters, characters / monsters, and topic pages. Source text expands as imports continue.',
      contentNote: 'Article bodies and source chapters stay in Chinese; language switch affects UI chrome and module labels only.',
      itemsFoldHint: 'Sections collapsed — click Expand all to show item cards',
      itemsEmpty: 'No artifact entries for this book yet.',
      itemsExtraPrefix: 'Medicine, food, costume & custom entities (',
      itemsExtraSuffix: ' total)',
      kaozhengEmpty: 'No textual-research topics yet. Add topics with category: 考证 under src/content/topics/.',
    },
    books: booksFor('en'),
    modules: moduleCopy.en,
  },
  ja: {
    siteTitle: '古典小説ナレッジベース',
    search: '検索',
    pageTitle: 'ホーム',
    subtitle: '中 国 古 典 小 説 · 知 識 グ ラ フ',
    title: '三大奇書',
    lead1: '只読の原文を根拠に、LLM が人物・関係・名物・版本を整理した知識图谱。',
    lead2: '貴族の挽歌、神魔の修行の旅、晚明世情を映す鏡。',
    booksMissingTitle: '書目カードを読み込めません',
    booksMissingBody:
      '開発モードでコンテンツ同期に失敗しました（Windows で dev 複数起動時に多い）。npm run dev:clean の後 dev を1つにするか、npm run build && npm run preview を使ってください。',
    enter: '入る →',
    footer: 'AGENTS.md に従い LLM が維持 · 原文は只読 · 事実と推論を分離',
    chapterUnit: '回',
    nav: { canon: '典籍', search: '検索', modules: 'モジュール' },
    ui: {
      exploreModules: 'モジュール',
      chapterIndex: '回目一覧',
      fullTextSearch: '全文検索',
      planned: '未実装',
      searchTitle: 'サイト内検索',
      searchLead: '取り込み済みの回目・人物/妖怪・トピックを検索。原文は順次拡充。',
      contentNote: '本文と章回原文は中国語のまま。言語切替は UI とモジュール説明のみに適用。',
      itemsFoldHint: '分類が折りたたまれています — 「全部展开」でカードを表示',
      itemsEmpty: '名物エントリはまだありません。',
      itemsExtraPrefix: '医薬・飲食・服飾・民俗エントリ（計',
      itemsExtraSuffix: '件）',
      kaozhengEmpty: '考証トピックがありません。src/content/topics/ に category: 考证 の topic を追加してください。',
    },
    books: booksFor('ja'),
    modules: moduleCopy.ja,
  },
} as const satisfies Record<SiteLocale, Record<string, unknown>>;

export type SiteMessages = (typeof messages)[SiteLocale];
