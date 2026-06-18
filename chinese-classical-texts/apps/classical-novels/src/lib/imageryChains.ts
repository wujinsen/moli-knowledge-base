/** B3 · 意象互文示例链路（*.imagery-chains.json） */

import type { ImageryGraph, ImageryGraphEdge } from './imagery';
import { HIGHLIGHT_CHAINS } from './imagery';

export interface ImageryChain {
  id: string;
  name: string;
  summary?: string;
  path: string[];
}

export interface ImageryChainHop {
  from: string;
  to: string;
  predicate?: string;
  inference?: boolean;
  chapter?: number;
  note?: string;
}

type ChainsFile = { book: string; chains: ImageryChain[] };

const chainFiles = import.meta.glob('../data/*.imagery-chains.json', { eager: true });

function fileForBook(bookName: string): ChainsFile | null {
  const key = Object.keys(chainFiles).find((k) => k.includes(bookName));
  if (!key) return null;
  const raw = chainFiles[key] as { default?: ChainsFile } & ChainsFile;
  return raw.default ?? raw;
}

/** 某书互文示例链路；优先 JSON，回退 HIGHLIGHT_CHAINS */
export function loadImageryChains(bookSlug: string, bookName: string): ImageryChain[] {
  const fromFile = fileForBook(bookName);
  if (fromFile?.chains?.length) return fromFile.chains;

  const legacy = HIGHLIGHT_CHAINS[bookSlug] ?? [];
  return legacy.map((c, i) => ({
    id: `legacy-${i}`,
    name: c.name,
    path: c.path,
  }));
}

function edgeBetween(a: string, b: string, edges: ImageryGraphEdge[]): ImageryGraphEdge | undefined {
  return edges.find(
    (e) => (e.source === a && e.target === b) || (e.source === b && e.target === a),
  );
}

/** 解析链路相邻节点间的图边（用于分步面板） */
export function resolveChainHops(path: string[], graph: ImageryGraph): ImageryChainHop[] {
  const hops: ImageryChainHop[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    const from = path[i];
    const to = path[i + 1];
    const edge = edgeBetween(from, to, graph.edges);
    hops.push({
      from,
      to,
      predicate: edge?.predicate,
      inference: edge?.inference,
      chapter: edge?.chapter,
      note: edge?.note,
    });
  }
  return hops;
}

export function chainIndexById(chains: ImageryChain[], id: string | null | undefined): number {
  if (!id) return 0;
  const idx = chains.findIndex((c) => c.id === id);
  return idx >= 0 ? idx : 0;
}
