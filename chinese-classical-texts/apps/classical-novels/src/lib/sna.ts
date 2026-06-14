export interface SnaMetric {
  id: string;
  degree: number;
  degree_norm: number;
  betweenness: number;
  faction?: string;
  ximen_proximity?: string;
  faction_rank?: number;
}

export interface SnaFactionSummary {
  count: number;
  top_betweenness: string[];
  max_degree: number;
}

export interface SnaData {
  book: string;
  generated?: string;
  node_count?: number;
  edge_count?: number;
  metrics: SnaMetric[];
  hubs: string[];
  bangxian_hubs?: string[];
  factions?: Record<string, SnaFactionSummary>;
  silver_links?: Record<string, string[]>;
}

export function proximityLabel(p?: string): string {
  return p ?? '—';
}

export function rankLabel(i: number): string {
  if (i === 0) return '枢纽';
  if (i < 3) return '高';
  if (i < 8) return '中';
  return '低';
}

export function filterMetrics(data: SnaData, faction?: string): SnaMetric[] {
  const list = faction ? data.metrics.filter((m) => m.faction === faction) : data.metrics;
  return [...list].sort((a, b) => {
    if (b.betweenness !== a.betweenness) return b.betweenness - a.betweenness;
    if (b.degree !== a.degree) return b.degree - a.degree;
    return a.id.localeCompare(b.id, 'zh');
  });
}

export function graphFocusHref(bookSlug: string, id: string): string {
  return `/${bookSlug}/graph?focus=${encodeURIComponent(id)}`;
}

export function characterHref(bookSlug: string, id: string): string {
  return `/${bookSlug}/c/${encodeURIComponent(id)}`;
}

export function silverHref(bookSlug: string, txId: string): string {
  return `/${bookSlug}/silver#${txId}`;
}
