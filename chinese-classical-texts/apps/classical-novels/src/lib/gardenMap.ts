/** 红楼梦大观园 M0 地图：纯数据与配色（不依赖 astro:content） */

export type GardenZone = '居所' | '水系' | '仪典' | '路径';

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
}

export interface GardenMapEdge {
  source: string;
  target: string;
  kind: 'tour' | 'nearby';
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
};

export const ZONE_LABELS: Record<GardenZone, string> = {
  居所: '居所',
  水系: '水系',
  仪典: '仪典轴',
  路径: '路径',
};

export function zoneColor(zone: GardenZone): string {
  return ZONE_COLORS[zone] ?? '#cbb37a';
}

/** 第17回游线顺序边 + nearby 邻接边 */
export function buildGardenEdges(nodes: GardenMapNode[]): GardenMapEdge[] {
  const ids = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: GardenMapEdge[] = [];

  const add = (source: string, target: string, kind: GardenMapEdge['kind']) => {
    if (!ids.has(source) || !ids.has(target) || source === target) return;
    const key = kind === 'tour' ? `${source}\0${target}\0tour` : [source, target].sort().join('\0') + kind;
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

  for (const n of nodes) {
    for (const nb of n.nearby) add(n.id, nb, 'nearby');
  }
  return edges;
}
