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

export interface TownMapData {
  nodes: TownMapNode[];
  edges: TownMapEdge[];
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
