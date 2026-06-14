/** 诗词意象 / 互文网络（纯函数，不含 astro:content） */

export interface ImageryLink {
  target: string;
  target_kind: 'character' | 'imagery';
  predicate: string;
  inference: boolean;
  chapter?: number;
  note?: string;
}

export interface ImageryData {
  id: string;
  subtype: string;
  title: string;
  text?: string;
  chapters: number[];
  characters: string[];
  links: ImageryLink[];
  summary?: string;
}

export type ImageryEntry = { data: ImageryData };

export interface ImageryGraphNode {
  id: string;
  label: string;
  kind: 'character' | 'judgment' | 'poem' | 'symbol' | 'flower_lot';
  size: number;
}

export interface ImageryGraphEdge {
  source: string;
  target: string;
  predicate: string;
  inference: boolean;
  chapter?: number;
  note?: string;
}

export interface ImageryGraph {
  nodes: ImageryGraphNode[];
  edges: ImageryGraphEdge[];
}

export const SUBTYPE_LABEL: Record<string, string> = {
  judgment: '判词',
  poem: '诗词',
  symbol: '象征',
  flower_lot: '花签',
  character: '人物',
};

export const HIGHLIGHT_CHAINS: { name: string; path: string[] }[] = [
  { name: '晴雯—芙蓉—黛玉', path: ['晴雯', 'hl-s-furong', '林黛玉'] },
  { name: '竹—潇湘—黛玉', path: ['hl-s-zhu', '林黛玉'] },
  { name: '金玉—钗黛', path: ['hl-s-yu', '贾宝玉', 'hl-s-jin', '薛宝钗'] },
  { name: '芙蓉诔—改字—黛玉', path: ['hl-p-05', '林黛玉', 'hl-s-furong', '晴雯'] },
  { name: '迎春—中山狼', path: ['hl-j-07', 'hl-p-19', '孙绍祖', '贾迎春'] },
  { name: '香菱—判词—咏月', path: ['hl-j-14', '香菱', 'hl-p-21'] },
];

const NODE_SIZE: Record<string, number> = {
  character: 28,
  judgment: 22,
  poem: 20,
  symbol: 24,
  flower_lot: 20,
};

function nodeKind(subtype: string | 'character'): ImageryGraphNode['kind'] {
  if (subtype === 'character') return 'character';
  return subtype as ImageryGraphNode['kind'];
}

function resolveTargetId(target: string, targetKind: string): string {
  return targetKind === 'imagery' ? target : target;
}

/** 从 imagery 实体 + 额外 JSON 边构建互文图 */
export function buildImageryGraph(
  items: ImageryEntry[],
  extraLinks: ImageryGraphEdge[] = [],
): ImageryGraph {
  const nodeMap = new Map<string, ImageryGraphNode>();
  const edges: ImageryGraphEdge[] = [...extraLinks];
  const edgeKeys = new Set(extraLinks.map((e) => `${e.source}|${e.predicate}|${e.target}`));

  const addNode = (id: string, label: string, kind: ImageryGraphNode['kind']) => {
    if (!nodeMap.has(id)) {
      nodeMap.set(id, { id, label, kind, size: NODE_SIZE[kind] ?? 20 });
    }
  };

  for (const item of items) {
    const d = item.data;
    addNode(d.id, d.title, nodeKind(d.subtype));
    for (const c of d.characters) {
      addNode(c, c, 'character');
    }
    for (const link of d.links) {
      const tid = resolveTargetId(link.target, link.target_kind);
      const tlabel = link.target_kind === 'imagery' ? link.target : link.target;
      addNode(tid, tlabel, link.target_kind === 'imagery' ? nodeKind('symbol') : 'character');
      const edge: ImageryGraphEdge = {
        source: d.id,
        target: tid,
        predicate: link.predicate,
        inference: link.inference,
        chapter: link.chapter,
        note: link.note,
      };
      const key = `${edge.source}|${edge.predicate}|${edge.target}`;
      if (!edgeKeys.has(key)) {
        edges.push(edge);
        edgeKeys.add(key);
      }
    }
  }

  for (const e of extraLinks) {
    addNode(e.source, e.source.startsWith('hl-') ? e.source : e.source, e.source.startsWith('hl-') ? 'symbol' : 'character');
    addNode(e.target, e.target, e.target.startsWith('hl-') ? 'symbol' : 'character');
  }

  // 修正 extra link 节点 label：用 items 里的 title
  for (const item of items) {
    const n = nodeMap.get(item.data.id);
    if (n) n.label = item.data.title;
  }

  return { nodes: [...nodeMap.values()], edges };
}

export function sortImagery(items: ImageryEntry[]): ImageryEntry[] {
  const order = ['judgment', 'poem', 'symbol', 'flower_lot'];
  return [...items].sort((a, b) => {
    const ia = order.indexOf(a.data.subtype);
    const ib = order.indexOf(b.data.subtype);
    if (ia !== ib) return ia - ib;
    return a.data.title.localeCompare(b.data.title, 'zh');
  });
}

export function subtypeLabel(subtype: string): string {
  return SUBTYPE_LABEL[subtype] ?? subtype;
}

export function chapterLabel(chapters: number[]): string {
  if (chapters.length === 0) return '—';
  if (chapters.length === 1) return `第${chapters[0]}回`;
  return `第${chapters[0]}–${chapters[chapters.length - 1]}回`;
}
