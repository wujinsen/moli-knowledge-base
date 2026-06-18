/** 红楼梦都外与王公地图（A9） */

export type CapitalZone = '都城' | '王府' | '侯伯' | '寺观' | '郊野' | '市井' | '连接';

export interface CapitalEventRef {
  id: string;
  title: string;
  chapters: number[];
  locations: string[];
}

export interface CapitalMapNode {
  id: string;
  name: string;
  zone: CapitalZone;
  category?: string;
  x: number;
  y: number;
  summary: string;
  chapters: number[];
  occupants: string[];
  plaque?: string;
  couplet?: { upper: string; lower: string };
  nearby: string[];
  events: CapitalEventRef[];
}

export type CapitalMapEdgeKind = 'nearby' | 'guide';

export interface CapitalMapEdge {
  source: string;
  target: string;
  kind: CapitalMapEdgeKind;
}

export interface CapitalMapData {
  nodes: CapitalMapNode[];
  edges: CapitalMapEdge[];
}

export const CAPITAL_ZONE_COLORS: Record<CapitalZone, string> = {
  都城: '#fbbf24',
  王府: '#c084fc',
  侯伯: '#a78bfa',
  寺观: '#34d399',
  郊野: '#86efac',
  市井: '#fb923c',
  连接: '#94a3b8',
};

export const CAPITAL_ZONE_LABELS: Record<CapitalZone, string> = {
  都城: '都城中枢',
  王府: '亲郡王府',
  侯伯: '侯伯驸马',
  寺观: '寺观祠庵',
  郊野: '郊野驿路',
  市井: '市井巷陌',
  连接: '宁荣接点',
};

export const CAPITAL_ZONE_ORDER: CapitalZone[] = [
  '都城',
  '王府',
  '侯伯',
  '寺观',
  '郊野',
  '市井',
  '连接',
];

export const CAPITAL_CHAPTER_PRESETS: { chapter: number | null; label: string }[] = [
  { chapter: null, label: '全部回目' },
  { chapter: 14, label: '第14回 · 路祭陈设' },
  { chapter: 15, label: '第15回 · 北静路祭' },
  { chapter: 16, label: '第16回 · 元春封妃' },
  { chapter: 29, label: '第29回 · 清虚观打醮' },
  { chapter: 33, label: '第33回 · 忠顺索琪官' },
  { chapter: 71, label: '第71回 · 王府寿宴' },
];

export const CAPITAL_GUIDES: { key: string; label: string; chapter: number; path: string[] }[] = [
  {
    key: 'ch14',
    label: '可卿路祭',
    chapter: 14,
    path: ['宁荣街', '十里屯', '铁槛寺', '北静王府'],
  },
  {
    key: 'ch29',
    label: '清虚观打醮',
    chapter: 29,
    path: ['宁荣街', '清虚观'],
  },
  {
    key: 'ch33',
    label: '忠顺索人',
    chapter: 33,
    path: ['宁荣街', '忠顺王府'],
  },
  {
    key: 'ch16',
    label: '元春封妃',
    chapter: 16,
    path: ['金陵城', '临敬殿'],
  },
];

export function capitalZoneColor(zone: CapitalZone): string {
  return CAPITAL_ZONE_COLORS[zone] ?? '#cbb37a';
}

export function buildCapitalGuideEdges(path: string[]): CapitalMapEdge[] {
  const edges: CapitalMapEdge[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    edges.push({ source: path[i], target: path[i + 1], kind: 'guide' });
  }
  return edges;
}

export function buildCapitalEdges(
  nodes: CapitalMapNode[],
  guidePath?: string[] | null,
): CapitalMapEdge[] {
  const ids = new Set(nodes.map((n) => n.id));
  const seen = new Set<string>();
  const edges: CapitalMapEdge[] = [];

  const add = (source: string, target: string, kind: CapitalMapEdgeKind) => {
    if (!ids.has(source) || !ids.has(target) || source === target) return;
    const key =
      kind === 'guide'
        ? `${source}\0${target}\0${kind}`
        : [source, target].sort().join('\0') + kind;
    if (seen.has(key)) return;
    seen.add(key);
    edges.push({ source, target, kind });
  };

  if (guidePath) {
    for (const e of buildCapitalGuideEdges(guidePath)) add(e.source, e.target, 'guide');
  }

  for (const n of nodes) {
    for (const nb of n.nearby) add(n.id, nb, 'nearby');
  }
  return edges;
}

export function attachCapitalEvents(
  nodes: CapitalMapNode[],
  events: CapitalEventRef[],
): CapitalMapNode[] {
  const byLoc = new Map<string, CapitalEventRef[]>();
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
