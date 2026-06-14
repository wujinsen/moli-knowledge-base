export interface FinancialEventNode {
  id: string;
  title: string;
  financial_kind: string;
  chapters: number[];
  chapter: number;
  characters: string[];
  locations: string[];
  amount_liang?: number | null;
  transaction_refs: string[];
  prev?: string;
  next?: string;
  summary: string;
  tags: string[];
}

export interface FinancialTrack {
  id: string;
  label: string;
  description: string;
  color: string;
  events: FinancialEventNode[];
  total_liang?: number | null;
  transaction_count: number;
}

export interface FinancialData {
  book: string;
  generated: string;
  event_count: number;
  timeline: FinancialEventNode[];
  tracks: FinancialTrack[];
  by_kind: Record<string, string[]>;
  events: FinancialEventNode[];
}

export function trackForEvent(data: FinancialData, eventId: string): FinancialTrack | undefined {
  return data.tracks.find((t) => t.events.some((e) => e.id === eventId));
}

export function eventHref(bookSlug: string, id: string): string {
  return `/${bookSlug}/e/${id}`;
}

export function silverHref(bookSlug: string, txId: string): string {
  return `/${bookSlug}/silver#${txId}`;
}
