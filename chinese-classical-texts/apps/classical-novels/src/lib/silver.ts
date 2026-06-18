import type { SankeyData } from './transactions';
import { POOL_COLORS } from './transactions';

export interface SilverTransaction {
  id: string;
  chapter: number;
  subtype: string;
  liang: number;
  pool_from: string;
  pool_to: string;
  disputed: boolean;
  summary: string;
}

export interface SilverPoolStat {
  name: string;
  inflow: number;
  outflow: number;
  net: number;
  depth: number;
  color: string;
}

export interface SilverTimelinePoint {
  chapter: number;
  delta: number;
  cumulative: number;
  tx_ids: string[];
}

export interface SilverData {
  book: string;
  generated: string;
  transaction_count: number;
  disputed_count: number;
  total_liang: number;
  chapter_min: number;
  chapter_max: number;
  hub: { name: string; inflow: number; outflow: number; net: number };
  pools: SilverPoolStat[];
  links: { source: string; target: string; value: number; txs: string[] }[];
  timeline: SilverTimelinePoint[];
  transactions: SilverTransaction[];
}

export { POOL_COLORS };

/** 将 hub 双向流合并为净额，供 ECharts 桑基（须 DAG）使用 */
export function collapseHubStarLinks(
  links: { source: string; target: string; value: number; txs: string[] }[],
  hub: string,
): { source: string; target: string; value: number; txs: string[] }[] {
  const neighbors = new Set<string>();
  for (const l of links) {
    if (l.source === hub || l.target === hub) {
      neighbors.add(l.source === hub ? l.target : l.source);
    }
  }

  const result: { source: string; target: string; value: number; txs: string[] }[] = [];
  for (const n of neighbors) {
    if (n === hub) continue;
    let toHub = 0;
    let fromHub = 0;
    const txsTo: string[] = [];
    const txsFrom: string[] = [];
    for (const l of links) {
      if (l.source === n && l.target === hub) {
        toHub += l.value;
        txsTo.push(...l.txs);
      } else if (l.source === hub && l.target === n) {
        fromHub += l.value;
        txsFrom.push(...l.txs);
      }
    }
    const net = Math.round((toHub - fromHub) * 100) / 100;
    if (Math.abs(net) < 0.001) continue;
    if (net > 0) {
      result.push({ source: n, target: hub, value: net, txs: txsTo });
    } else {
      result.push({ source: hub, target: n, value: -net, txs: txsFrom });
    }
  }
  return result;
}

function sankeyDepth(
  name: string,
  hub: string,
  links: { source: string; target: string }[],
): number {
  if (name === hub) return 1;
  if (links.some((l) => l.target === hub && l.source === name)) return 0;
  return 2;
}

function buildSilverSlice(data: SilverData, txs: SilverTransaction[]): SilverData {
  const linkMap = new Map<string, { value: number; txs: string[] }>();

  for (const t of txs) {
    const key = `${t.pool_from}→${t.pool_to}`;
    const prev = linkMap.get(key) ?? { value: 0, txs: [] };
    prev.value += t.liang;
    prev.txs.push(t.id);
    linkMap.set(key, prev);
  }

  const poolOut = new Map<string, number>();
  const poolIn = new Map<string, number>();
  const hubIn = new Map<string, number>();
  const hubOut = new Map<string, number>();
  const hub = data.hub.name;

  for (const t of txs) {
    poolOut.set(t.pool_from, (poolOut.get(t.pool_from) ?? 0) + t.liang);
    poolIn.set(t.pool_to, (poolIn.get(t.pool_to) ?? 0) + t.liang);
    if (t.pool_to === hub) hubIn.set(t.pool_from, (hubIn.get(t.pool_from) ?? 0) + t.liang);
    if (t.pool_from === hub) hubOut.set(t.pool_to, (hubOut.get(t.pool_to) ?? 0) + t.liang);
  }

  const poolNames = new Set([...poolOut.keys(), ...poolIn.keys()]);
  const pools = [...poolNames].map((name) => {
    const base = data.pools.find((p) => p.name === name);
    const inf = Math.round((poolIn.get(name) ?? 0) * 100) / 100;
    const outf = Math.round((poolOut.get(name) ?? 0) * 100) / 100;
    return {
      name,
      inflow: inf,
      outflow: outf,
      net: Math.round((inf - outf) * 100) / 100,
      depth: base?.depth ?? (name === hub ? 1 : 2),
      color: base?.color ?? POOL_COLORS[name] ?? '#607a67',
    };
  });

  const links = [...linkMap.entries()].map(([key, v]) => {
    const [source, target] = key.split('→');
    return { source, target, value: Math.round(v.value * 100) / 100, txs: v.txs };
  });

  const byCh = new Map<number, string[]>();
  for (const t of txs) {
    const list = byCh.get(t.chapter) ?? [];
    list.push(t.id);
    byCh.set(t.chapter, list);
  }
  const timeline: SilverTimelinePoint[] = [];
  let cumulative = 0;
  for (const ch of [...byCh.keys()].sort((a, b) => a - b)) {
    const chTxs = txs.filter((t) => t.chapter === ch);
    const delta = chTxs.reduce((s, t) => s + t.liang, 0);
    cumulative += delta;
    timeline.push({
      chapter: ch,
      delta: Math.round(delta * 100) / 100,
      cumulative: Math.round(cumulative * 100) / 100,
      tx_ids: byCh.get(ch)!,
    });
  }

  return {
    ...data,
    transaction_count: txs.length,
    disputed_count: txs.filter((t) => t.disputed).length,
    total_liang: timeline.length ? timeline[timeline.length - 1].cumulative : 0,
    pools,
    links,
    timeline,
    transactions: txs,
    hub: {
      name: hub,
      inflow: Math.round([...hubIn.values()].reduce((s, v) => s + v, 0) * 100) / 100,
      outflow: Math.round([...hubOut.values()].reduce((s, v) => s + v, 0) * 100) / 100,
      net: Math.round(
        ([...hubIn.values()].reduce((s, v) => s + v, 0) -
          [...hubOut.values()].reduce((s, v) => s + v, 0)) *
          100,
      ) / 100,
    },
  };
}

export function filterSilverByChapter(data: SilverData, maxChapter: number): SilverData {
  const txs = data.transactions.filter((t) => t.chapter <= maxChapter && t.liang > 0);
  return buildSilverSlice(data, txs);
}

export function filterSilverByTrack(data: SilverData, txIds: Set<string> | null): SilverData {
  if (!txIds?.size) return data;
  const txs = data.transactions.filter((t) => txIds.has(t.id) && t.liang > 0);
  return buildSilverSlice(data, txs);
}

export function filterSilver(
  data: SilverData,
  opts: { maxChapter?: number; trackTxIds?: Set<string> | null },
): SilverData {
  let txs = data.transactions.filter((t) => t.liang > 0);
  if (opts.maxChapter != null) txs = txs.filter((t) => t.chapter <= opts.maxChapter);
  if (opts.trackTxIds?.size) txs = txs.filter((t) => opts.trackTxIds!.has(t.id));
  return buildSilverSlice(data, txs);
}

export function toSankey(data: SilverData): SankeyData {
  const hub = data.hub.name;
  const dagLinks = collapseHubStarLinks(data.links, hub);
  const nodeNames = new Set<string>([hub]);
  for (const l of dagLinks) {
    nodeNames.add(l.source);
    nodeNames.add(l.target);
  }
  return {
    nodes: [...nodeNames].map((name) => {
      const p = data.pools.find((x) => x.name === name);
      return {
        name,
        depth: sankeyDepth(name, hub, dagLinks),
        value: p ? Math.max(p.inflow, p.outflow) : 0,
      };
    }),
    links: dagLinks.map((l) => ({
      source: l.source,
      target: l.target,
      value: l.value,
      txs: l.txs,
    })),
  };
}

/** Re-export depth on nodes for ECharts — SankeyData nodes extended at runtime */
export type SankeyNodeWithDepth = { name: string; depth?: number; value?: number };
