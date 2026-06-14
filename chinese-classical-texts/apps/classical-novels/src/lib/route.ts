/** 取经路线 GIS：纯数据与配色（不依赖 astro:content） */

export type RouteLayer = 'real' | 'myth';

export interface RouteTribulation {
  id: string;
  no: number;
  title: string;
}

export interface RouteNode {
  id: string;
  name: string;
  realm: string;
  layer: RouteLayer;
  x: number;
  y: number;
  order: number | null;
  aliases: string[];
  summary: string;
  chapters: number[];
  tribulations: RouteTribulation[];
}

export interface RouteEdge {
  source: string;
  target: string;
}

export interface RouteData {
  nodes: RouteNode[];
  edges: RouteEdge[];
}

/** 地理区域 → 描金/异色（深色舞台高对比） */
export const REALM_COLORS: Record<string, string> = {
  凡间: '#e0a93a',
  灵山: '#f6df9a',
  天界: '#5eb6e6',
  南海: '#37c98d',
  东海: '#22c1d6',
  地府: '#9b87f5',
};

export function realmColor(realm: string): string {
  return REALM_COLORS[realm] ?? '#cbb37a';
}

export const LAYER_LABELS: Record<RouteLayer, string> = {
  real: '凡间路线',
  myth: '神话地理',
};

/** 由凡间节点的 route_order 串成取经折线 */
export function buildRouteEdges(nodes: RouteNode[]): RouteEdge[] {
  const path = nodes
    .filter((n) => n.layer === 'real' && n.order != null)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
  const edges: RouteEdge[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    edges.push({ source: path[i].id, target: path[i + 1].id });
  }
  return edges;
}
