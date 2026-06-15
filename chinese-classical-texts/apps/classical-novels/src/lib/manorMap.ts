/** 红楼梦宁荣两府地图（M3） */

export type ManorZone = '荣府轴' | '荣府侧' | '宁府轴' | '宁府园' | '连接' | '外联';

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
}

export interface ManorMapEdge {
  source: string;
  target: string;
  kind: 'axis' | 'nearby';
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

/** 第3回黛玉入府叙事序（fact 游线示意） */
export const MANOR_AXIS_PATH = [
  '宁荣街',
  '荣国府',
  '荣禧堂',
  '贾母上房',
  '贾政上房',
  '王夫人上房',
];

export function manorZoneColor(zone: ManorZone): string {
  return MANOR_ZONE_COLORS[zone] ?? '#cbb37a';
}

export function buildManorEdges(nodes: ManorMapNode[]): ManorMapEdge[] {
  const ids = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: ManorMapEdge[] = [];

  const add = (source: string, target: string, kind: ManorMapEdge['kind']) => {
    if (!ids.has(source) || !ids.has(target) || source === target) return;
    const key = kind === 'axis' ? `${source}\0${target}\0axis` : [source, target].sort().join('\0');
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({ source, target, kind });
  };

  const axisIds = MANOR_AXIS_PATH.filter((id) => ids.has(id));
  for (let i = 0; i < axisIds.length - 1; i++) {
    add(axisIds[i], axisIds[i + 1], 'axis');
  }

  for (const n of nodes) {
    for (const nb of n.nearby) add(n.id, nb, 'nearby');
  }
  return edges;
}
