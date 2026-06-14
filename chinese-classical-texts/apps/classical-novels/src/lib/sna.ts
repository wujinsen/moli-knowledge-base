export interface SnaMetric {
  id: string;
  degree: number;
  degree_norm: number;
  betweenness: number;
  faction?: string;
  ximen_proximity?: string;
}

export interface SnaData {
  book: string;
  metrics: SnaMetric[];
  hubs: string[];
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
