import { formatLiang } from './currency';

export interface TxData {
  id: string;
  subtype: string;
  amount: number;
  currency: string;
  amount_normalized?: number | null;
  conversion_disputed?: boolean;
  buyer?: string;
  seller?: string;
  payee?: string;
  chapter: number;
  summary?: string;
  pool_from: string;
  pool_to: string;
}

export type TxEntry = { data: TxData };

export const POOL_COLORS: Record<string, string> = {
  西门庆府: '#607a67',
  蔡太师府: '#8a6532',
  外部: '#9c8450',
  妻妾奴婢: '#74332c',
  帮闲圈: '#5c6359',
  经营投资: '#33493c',
  外室: '#6c8576',
  宗教布施: '#266c7c',
  官场打点: '#8a6a3b',
  官府: '#4a5568',
  玉皇庙: '#5a7a6a',
  清河县: '#7a6a5a',
};

export function effectiveLiang(d: TxData): number {
  return d.amount_normalized ?? 0;
}

export interface SankeyData {
  nodes: { name: string; depth?: number; value?: number }[];
  links: { source: string; target: string; value: number; txs: string[] }[];
}

/** 按资金池聚合桑基图数据 */
export function buildSankey(transactions: TxEntry[]): SankeyData {
  const linkMap = new Map<string, { value: number; txs: string[] }>();

  for (const t of transactions) {
    const v = effectiveLiang(t.data);
    if (v <= 0) continue;
    const key = `${t.data.pool_from}→${t.data.pool_to}`;
    const prev = linkMap.get(key) ?? { value: 0, txs: [] };
    prev.value += v;
    prev.txs.push(t.data.id);
    linkMap.set(key, prev);
  }

  const nodeSet = new Set<string>();
  const links = [...linkMap.entries()].map(([key, { value, txs }]) => {
    const [source, target] = key.split('→');
    nodeSet.add(source);
    nodeSet.add(target);
    return { source, target, value: Math.round(value * 100) / 100, txs };
  });

  return {
    nodes: [...nodeSet].map((name) => ({ name })),
    links,
  };
}

export function poolTotals(transactions: TxEntry[]) {
  const out = new Map<string, number>();
  const inn = new Map<string, number>();
  for (const t of transactions) {
    const v = effectiveLiang(t.data);
    if (v <= 0) continue;
    out.set(t.data.pool_from, (out.get(t.data.pool_from) ?? 0) + v);
    inn.set(t.data.pool_to, (inn.get(t.data.pool_to) ?? 0) + v);
  }
  return { out, inn };
}

export function subtypeLabel(subtype: string): string {
  return subtype;
}

export function amountDisplay(d: TxData): string {
  const raw = `${d.amount}${d.currency}`;
  if (d.amount_normalized != null) {
    return `${raw} → ${formatLiang(d.amount_normalized)}`;
  }
  return raw;
}
