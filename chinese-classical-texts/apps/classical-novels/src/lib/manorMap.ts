/** 红楼梦宁荣两府地图（M3/M4） */

export type ManorZone = '荣府轴' | '荣府侧' | '宁府轴' | '宁府园' | '连接' | '外联';

export interface ManorEventRef {
  id: string;
  title: string;
  chapters: number[];
  locations: string[];
}

export interface ManorMapNode {
  id: string;
  name: string;
  zone: ManorZone;
  category?: string;
  x: number;
  y: number;
  summary: string;
  chapters: number[];
  occupants: string[];
  plaque?: string;
  couplet?: { upper: string; lower: string };
  nearby: string[];
  events: ManorEventRef[];
}

export type ManorMapEdgeKind = 'axis' | 'ningAxis' | 'nearby' | 'guide';

export interface ManorMapEdge {
  source: string;
  target: string;
  kind: ManorMapEdgeKind;
}

export interface ManorMapData {
  nodes: ManorMapNode[];
  edges: ManorMapEdge[];
}

export const MANOR_ZONE_COLORS: Record<ManorZone, string> = {
  荣府轴: '#e879a8',
  荣府侧: '#f472b6',
  宁府轴: '#5eb6e6',
  宁府园: '#38bdf8',
  连接: '#94a3b8',
  外联: '#a78bfa',
};

export const MANOR_ZONE_LABELS: Record<ManorZone, string> = {
  荣府轴: '荣府礼制轴',
  荣府侧: '荣府侧院',
  宁府轴: '宁府中轴',
  宁府园: '宁府园林',
  连接: '门禁连接',
  外联: '祠塾外联',
};

export const MANOR_ZONE_ORDER: ManorZone[] = [
  '荣府轴',
  '荣府侧',
  '宁府轴',
  '宁府园',
  '连接',
  '外联',
];

/** 第3回黛玉入府 · 荣府礼制轴（fact 叙事序） */
export const MANOR_AXIS_PATH = [
  '宁荣街',
  '荣国府',
  '荣禧堂',
  '贾母上房',
  '王夫人上房',
  '贾政上房',
];

/** 宁府丧祭 / 内宅轴（inference） */
export const MANOR_NING_AXIS_PATH = [
  '宁国府',
  '尤氏上房',
  '邢夫人上房',
  '可卿上房',
  '会芳园',
  '天香楼',
];

/** 第53回主仆分界 · 门禁层级（fact） */
export const MANOR_GATE_PATH = ['门上', '二门', '仪门', '穿堂'];

export const MANOR_CHAPTER_PRESETS: { chapter: number | null; label: string }[] = [
  { chapter: null, label: '全部回目' },
  { chapter: 3, label: '第3回 · 黛玉入府' },
  { chapter: 4, label: '第4回 · 薛家进府' },
  { chapter: 7, label: '第7回 · 送宫花' },
  { chapter: 13, label: '第13回 · 可卿大丧' },
  { chapter: 53, label: '第53回 · 开宗祠' },
  { chapter: 55, label: '第55回 · 探春理家' },
];

/** 预设导览线（M4） */
export const MANOR_GUIDES: { key: string; label: string; chapter: number; path: string[] }[] = [
  {
    key: 'ch3',
    label: '黛玉入府',
    chapter: 3,
    path: ['宁荣街', '荣国府', '荣禧堂', '贾母上房', '王夫人上房', '贾政上房'],
  },
  {
    key: 'gate',
    label: '门禁层级',
    chapter: 53,
    path: MANOR_GATE_PATH,
  },
  {
    key: 'ch53',
    label: '开宗祠',
    chapter: 53,
    path: ['贾氏宗祠', '宁国府', '会芳园', '荣国府'],
  },
  {
    key: 'ch13',
    label: '可卿大丧',
    chapter: 13,
    path: ['宁国府', '尤氏上房', '天香楼', '会芳园'],
  },
  {
    key: 'ch4',
    label: '薛家寄居',
    chapter: 4,
    path: ['荣国府', '东角门', '梨香院'],
  },
];

export function manorZoneColor(zone: ManorZone): string {
  return MANOR_ZONE_COLORS[zone] ?? '#cbb37a';
}

export function buildManorGuideEdges(path: string[]): ManorMapEdge[] {
  const edges: ManorMapEdge[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    edges.push({ source: path[i], target: path[i + 1], kind: 'guide' });
  }
  return edges;
}

export function buildManorEdges(
  nodes: ManorMapNode[],
  guidePath?: string[] | null,
): ManorMapEdge[] {
  const ids = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: ManorMapEdge[] = [];

  const add = (source: string, target: string, kind: ManorMapEdgeKind) => {
    if (!ids.has(source) || !ids.has(target) || source === target) return;
    const key =
      kind === 'axis' || kind === 'ningAxis' || kind === 'guide'
        ? `${source}\0${target}\0${kind}`
        : [source, target].sort().join('\0') + kind;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({ source, target, kind });
  };

  const axisIds = MANOR_AXIS_PATH.filter((id) => ids.has(id));
  for (let i = 0; i < axisIds.length - 1; i++) {
    add(axisIds[i], axisIds[i + 1], 'axis');
  }

  const ningIds = MANOR_NING_AXIS_PATH.filter((id) => ids.has(id));
  for (let i = 0; i < ningIds.length - 1; i++) {
    add(ningIds[i], ningIds[i + 1], 'ningAxis');
  }

  if (guidePath) {
    for (const e of buildManorGuideEdges(guidePath)) add(e.source, e.target, 'guide');
  }

  for (const n of nodes) {
    for (const nb of n.nearby) add(n.id, nb, 'nearby');
  }
  return edges;
}

export function attachManorEvents(
  nodes: ManorMapNode[],
  events: ManorEventRef[],
): ManorMapNode[] {
  const byLoc = new Map<string, ManorEventRef[]>();
  for (const ev of events) {
    for (const loc of ev.locations) {
      if (!byLoc.has(loc)) byLoc.set(loc, []);
      byLoc.get(loc)!.push(ev);
    }
  }
  return nodes.map((n) => ({
    ...n,
    events: byLoc.get(n.id) ?? [],
  }));
}
