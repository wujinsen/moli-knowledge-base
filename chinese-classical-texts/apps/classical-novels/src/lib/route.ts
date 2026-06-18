import { canvasBearing, formatSegment, type GeoPoint } from './routeGeo';

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
  geo?: { lat: number; lng: number };
  order: number | null;
  aliases: string[];
  summary: string;
  chapters: number[];
  tribulations: RouteTribulation[];
}

export interface RouteEdge {
  source: string;
  target: string;
  /** 路段距离（km，丝路比附） */
  distanceKm?: number;
  /** 传统里数（丝路比附） */
  distanceLi?: number;
  /** 丝路相对方位 */
  bearing?: string;
  /** 示意图画布上的走向 */
  schematicBearing?: string;
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

/** 由凡间节点的 route_order 串成取经折线，并标注相对方位与距离 */
export function buildRouteEdges(nodes: RouteNode[]): RouteEdge[] {
  const path = nodes
    .filter((n) => n.layer === 'real' && n.order != null)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
  const edges: RouteEdge[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    const a = path[i];
    const b = path[i + 1];
    const edge: RouteEdge = { source: a.id, target: b.id };
    if (a.geo && b.geo) {
      const seg = formatSegment(a.geo as GeoPoint, b.geo as GeoPoint);
      edge.distanceKm = seg.km;
      edge.distanceLi = seg.li;
      edge.bearing = seg.bearing;
    }
    edge.schematicBearing = canvasBearing(a, b);
    edges.push(edge);
  }
  return edges;
}
