/** C2 发家衰败链 P3–P4：构建期 chain.json 索引 */

import chainJson from '../data/jinpingmei.chain.json';

export interface TxChip {
  liang: number;
  summary: string;
  subtype: string;
  chapter: number;
  disputed: boolean;
}

export interface ChainEventRow {
  id: string;
  title: string;
  subtype: string;
  financial_kind: string;
  chapters: number[];
  chapter: number;
  phase: string;
  phase_label: string;
  amount_liang?: number | null;
  summary: string;
  characters: string[];
  locations: string[];
  transaction_refs: string[];
  prev?: string | null;
  next?: string | null;
  tags: string[];
  module_links: {
    graph_focus?: string | null;
    has_silver: boolean;
    has_sna: boolean;
  };
}

export interface ChainPhase {
  key: string;
  label: string;
  range: [number, number];
  count: number;
}

export interface ChainIndex {
  book: string;
  generated: string;
  event_count: number;
  financial_count: number;
  plot_count: number;
  phases: ChainPhase[];
  tx_chips: Record<string, TxChip>;
  by_character: Record<string, string[]>;
  events: ChainEventRow[];
}

const INDEX = chainJson as ChainIndex;

export function getChainIndex(bookSlug: string): ChainIndex | null {
  return bookSlug === 'jinpingmei' ? INDEX : null;
}

export function chainEventsForCharacter(bookSlug: string, charId: string): ChainEventRow[] {
  const idx = getChainIndex(bookSlug);
  if (!idx) return [];
  const ids = idx.by_character[charId] ?? [];
  const byId = new Map(idx.events.map((e) => [e.id, e]));
  return ids.map((id) => byId.get(id)).filter(Boolean) as ChainEventRow[];
}

export function txChipLabel(chip: TxChip | undefined, txId: string): string {
  if (!chip) return txId;
  const short = chip.summary.length > 14 ? `${chip.summary.slice(0, 14)}…` : chip.summary;
  return `${chip.liang}两 · ${short || chip.subtype || txId}`;
}

export { INDEX as jpmChainIndex };
