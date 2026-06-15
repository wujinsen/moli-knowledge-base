/** 红楼梦大观园地图：纯数据与配色（不依赖 astro:content） */

export type GardenZone = '居所' | '水系' | '仪典' | '路径' | '亭榭' | '寺观' | '服务';

export interface GardenEventRef {
  id: string;
  title: string;
  chapters: number[];
  locations: string[];
}

export interface GardenMapNode {
  id: string;
  name: string;
  zone: GardenZone;
  category?: string;
  x: number;
  y: number;
  tourOrder: number | null;
  summary: string;
  chapters: number[];
  occupants: string[];
  plants: string[];
  plaque?: string;
  couplet?: { upper: string; lower: string };
  nearby: string[];
  events: GardenEventRef[];
}

export interface GardenMapEdge {
  source: string;
  target: string;
  kind: 'tour' | 'nearby' | 'guide';
}

export interface GardenMapData {
  nodes: GardenMapNode[];
  edges: GardenMapEdge[];
}

export const ZONE_COLORS: Record<GardenZone, string> = {
  居所: '#e879a8',
  水系: '#5eb6e6',
  仪典: '#d4a017',
  路径: '#94a3b8',
  亭榭: '#a78bfa',
  寺观: '#7c9cbf',
  服务: '#64748b',
};

export const ZONE_LABELS: Record<GardenZone, string> = {
  居所: '居所',
  水系: '水系',
  仪典: '仪典轴',
  路径: '路径',
  亭榭: '亭榭堂馆',
  寺观: '庵庙',
  服务: '后勤',
};

export const ZONE_ORDER: GardenZone[] = ['居所', '水系', '仪典', '路径', '亭榭', '寺观', '服务'];

/** 回目快捷筛选（M1/M2） */
export const GARDEN_CHAPTER_PRESETS: { chapter: number | null; label: string }[] = [
  { chapter: null, label: '全部回目' },
  { chapter: 17, label: '第17回 · 题额游园' },
  { chapter: 23, label: '第23回 · 分房入住' },
  { chapter: 38, label: '第38回 · 螃蟹宴' },
  { chapter: 40, label: '第40回 · 刘姥姥' },
  { chapter: 42, label: '第42回 · 湘云醉卧' },
  { chapter: 56, label: '第56回 · 凸凹晶馆' },
  { chapter: 74, label: '第74回 · 抄检' },
];

/** 预设导览线（M2） */
export const GARDEN_GUIDES: { key: string; label: string; chapter: number; path: string[] }[] = [
  {
    key: 'ch17',
    label: '贾政游园',
    chapter: 17,
    path: [
      '曲径通幽', '沁芳亭', '潇湘馆', '稻香村', '蓼溆', '蘅芜苑',
      '省亲别墅', '沁芳闸', '怡红院',
    ],
  },
  {
    key: 'liulaolao',
    label: '刘姥姥导览',
    chapter: 40,
    path: ['曲径通幽', '沁芳亭', '潇湘馆', '秋爽斋', '蘅芜苑', '怡红院'],
  },
  {
    key: 'ch23',
    label: '分房入住',
    chapter: 23,
    path: ['潇湘馆', '怡红院', '蘅芜苑', '稻香村', '秋爽斋', '缀锦楼', '蓼风轩'],
  },
  {
    key: 'ch38',
    label: '螃蟹宴',
    chapter: 38,
    path: ['沁芳亭', '藕香榭'],
  },
];

export function zoneColor(zone: GardenZone): string {
  return ZONE_COLORS[zone] ?? '#cbb37a';
}

export function buildGuideEdges(path: string[]): GardenMapEdge[] {
  const edges: GardenMapEdge[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    edges.push({ source: path[i], target: path[i + 1], kind: 'guide' });
  }
  return edges;
}

/** 第17回游线 + nearby + 可选导览线 */
export function buildGardenEdges(
  nodes: GardenMapNode[],
  guidePath?: string[] | null,
): GardenMapEdge[] {
  const ids = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: GardenMapEdge[] = [];

  const add = (source: string, target: string, kind: GardenMapEdge['kind']) => {
    if (!ids.has(source) || !ids.has(target) || source === target) return;
    const key =
      kind === 'tour' || kind === 'guide'
        ? `${source}\0${target}\0${kind}`
        : [source, target].sort().join('\0') + kind;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({ source, target, kind });
  };

  const tour = [...nodes]
    .filter((n) => n.tourOrder != null)
    .sort((a, b) => (a.tourOrder ?? 0) - (b.tourOrder ?? 0));
  for (let i = 0; i < tour.length - 1; i++) {
    add(tour[i].id, tour[i + 1].id, 'tour');
  }

  if (guidePath) {
    for (const e of buildGuideEdges(guidePath)) add(e.source, e.target, 'guide');
  }

  for (const n of nodes) {
    for (const nb of n.nearby) add(n.id, nb, 'nearby');
  }
  return edges;
}

/** 将 milestone 事件按 locations 挂到园内节点 */
export function attachEventsToNodes(
  nodes: GardenMapNode[],
  events: GardenEventRef[],
): GardenMapNode[] {
  const byLoc = new Map<string, GardenEventRef[]>();
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
