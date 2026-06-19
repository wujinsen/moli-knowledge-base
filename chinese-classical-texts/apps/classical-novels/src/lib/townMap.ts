/** 金瓶梅市井地图：纯数据与配色（不依赖 astro:content） */

export type TownZone = '府内' | '市井' | '寺观' | '城外';

export interface TownEventRef {
  id: string;
  title: string;
  subtype: string;
  chapters: number[];
}

export interface TownMapNode {
  id: string;
  name: string;
  zone: TownZone;
  category?: string;
  x: number;
  y: number;
  parent?: string;
  summary: string;
  chapters: number[];
  items: string[];
  events: TownEventRef[];
  nearby: string[];
}

export interface TownMapEdge {
  source: string;
  target: string;
  kind: 'nearby' | 'parent';
}

export interface TownRouteStop {
  id: string;
  name: string;
  zone: TownZone;
  x: number;
  y: number;
}

/** 事件路线：一条有序的地点路径，渲染为 GIS 图上的折线 + 编号停靠点 */
export interface TownRoute {
  id: string;
  title: string;
  subtype: string;
  chapters: number[];
  summary: string;
  stops: TownRouteStop[];
}

export interface TownMapData {
  nodes: TownMapNode[];
  edges: TownMapEdge[];
  routes?: TownRoute[];
}

export interface TownGisMeta {
  bounds: { width: number; height: number };
  scale_note: string;
  zone_hulls: Partial<Record<TownZone, number[][]>>;
}

/** Simple CRS：存储 x 东 / y 南 → Leaflet [lat, lng] = [y, x] */
export function toLeafletLatLng(x: number, y: number, _height?: number): [number, number] {
  return [y, x];
}

export const ZONE_COLORS: Record<TownZone, string> = {
  府内: '#d4a017',
  市井: '#37c98d',
  寺观: '#9b87f5',
  城外: '#5eb6e6',
};

export const ZONE_LABELS: Record<TownZone, string> = {
  府内: '西门府内',
  市井: '清河县井',
  寺观: '寺观',
  城外: '政商远端',
};

export function zoneColor(zone: TownZone): string {
  return ZONE_COLORS[zone] ?? '#cbb37a';
}

const GIS_HUBS = new Set(['清河县', '西门府', '狮子街', '县衙', '县前街']);

function nodeDist(a: TownMapNode, b: TownMapNode): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

/** GIS 层：只保留隶属边 + 短距邻接，避免 nearby 全量成「毛线球」 */
export function buildTownGisEdges(nodes: TownMapNode[]): TownMapEdge[] {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const seen = new Set<string>();
  const edges: TownMapEdge[] = [];

  const add = (source: string, target: string, kind: TownMapEdge['kind']) => {
    if (source === target) return;
    const a = byId.get(source);
    const b = byId.get(target);
    if (!a || !b) return;
    const key = [source, target].sort().join('\0') + kind;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({ source, target, kind });
  };

  for (const n of nodes) {
    if (n.parent) add(n.parent, n.id, 'parent');
  }

  const SAME_ZONE_MAX = 48;
  const HUB_LINK_MAX = 72;

  for (const n of nodes) {
    const scored: { id: string; d: number }[] = [];
    for (const nb of n.nearby) {
      const other = byId.get(nb);
      if (!other) continue;
      const d = nodeDist(n, other);
      if (n.zone === other.zone && d <= SAME_ZONE_MAX) {
        scored.push({ id: nb, d });
      } else if ((GIS_HUBS.has(n.id) || GIS_HUBS.has(other.id)) && d <= HUB_LINK_MAX) {
        scored.push({ id: nb, d });
      }
    }
    scored.sort((a, b) => a.d - b.d);
    for (const { id } of scored.slice(0, 2)) add(n.id, id, 'nearby');
  }

  return edges;
}

/** 默认视野：清河县城 + 西门府 + 近郊（不含杭州/东京等远端） */
export function filterTownGisCoreNodes(nodes: TownMapNode[]): TownMapNode[] {
  return nodes.filter(
    (n) =>
      n.zone !== '城外' ||
      ['临清钞关', '临清酒店', '皇庄', '内相花园', '东平府'].includes(n.id),
  );
}

/** 政商全图：清河区域只保留枢纽，避免 50+ 点叠成一团 */
export const GIS_FULL_HUBS = new Set([
  '清河县',
  '西门府',
  '狮子街',
  '县衙',
  '县前街',
  '玉皇庙',
  '永福寺',
  '临清钞关',
  '皇庄',
]);

/** 政商全图模式下额外强调标注的远端节点 */
export const GIS_REMOTE_LABELS = new Set([
  '东京',
  '蔡府',
  '杭州',
  '扬州',
  '怀庆府',
  '东昌府',
  '临清钞关',
  '临清酒店',
]);

export function baseGisMarkerRadius(n: TownMapNode, coreIds: Set<string>): number {
  const isHub = n.id === '西门府' || n.id === '清河县';
  const isRemote = n.zone === '城外' && !coreIds.has(n.id);
  if (isHub) return 8;
  if (isRemote) return 5;
  return n.zone === '府内' ? 4 : 5;
}

/** 由 parent + nearby 生成示意边 */
export function buildTownEdges(nodes: TownMapNode[]): TownMapEdge[] {
  const ids = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: TownMapEdge[] = [];

  const add = (source: string, target: string, kind: TownMapEdge['kind']) => {
    if (!ids.has(source) || !ids.has(target) || source === target) return;
    const key = [source, target].sort().join('\0') + kind;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({ source, target, kind });
  };

  for (const n of nodes) {
    if (n.parent) add(n.parent, n.id, 'parent');
    for (const nb of n.nearby) add(n.id, nb, 'nearby');
  }
  return edges;
}
