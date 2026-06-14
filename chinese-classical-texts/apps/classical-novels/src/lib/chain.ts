/** 发家衰败链 · 跨模块互链（P3/P4） */

export function chainEventHref(bookSlug: string, eventId: string): string {
  return `/${bookSlug}/chain?focus=${encodeURIComponent(eventId)}`;
}

export function silverEventHref(bookSlug: string, eventId: string): string {
  return `/${bookSlug}/silver?event=${encodeURIComponent(eventId)}`;
}

export function silverTxHref(bookSlug: string, txId: string): string {
  return `/${bookSlug}/silver#${txId}`;
}

export function pickGraphFocus(
  characters: string[],
  hubs: string[] = [],
  bangxianHubs: string[] = [],
): string | undefined {
  const priority = new Set([...bangxianHubs, ...hubs]);
  for (const c of characters) {
    if (priority.has(c)) return c;
  }
  return characters[0];
}

export interface ChainEventLinks {
  graphFocus?: string;
  hasSilver: boolean;
  hasSna: boolean;
}

export function chainEventLinks(
  characters: string[],
  transactionRefs: string[],
  opts: { hubs?: string[]; bangxianHubs?: string[]; features: string[] },
): ChainEventLinks {
  const graphFocus = pickGraphFocus(characters, opts.hubs, opts.bangxianHubs);
  return {
    graphFocus,
    hasSilver: transactionRefs.length > 0 && opts.features.includes('silver'),
    hasSna: !!graphFocus && opts.features.includes('sna'),
  };
}
