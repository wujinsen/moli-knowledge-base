import hlmCrosslinks from '../data/hongloumeng.crosslinks.json';
import jpmCrosslinks from '../data/jinpingmei.crosslinks.json';
import xyjCrosslinks from '../data/xiyouji.crosslinks.json';
import { loadEvents } from './loadEvents';
import { loadTransactions } from './loadTransactions';
import { loadBookItems, type ItemEntry } from './items';

export type ItemRef = { id: string; name: string; kind: ItemEntry['kind'] };

export type TransactionRef = {
  id: string;
  summary: string;
  chapter: number;
  amount?: string;
};

type CrosslinksFile = {
  book: string;
  location_items: Record<string, string[]>;
  occupant_items: Record<string, string[]>;
  occupant_transactions?: Record<string, string[]>;
};

const CROSSLINKS: Record<string, CrosslinksFile> = {
  红楼梦: hlmCrosslinks as CrosslinksFile,
  西游记: xyjCrosslinks as CrosslinksFile,
  金瓶梅: jpmCrosslinks as CrosslinksFile,
};

function crosslinksFor(book: string): CrosslinksFile | undefined {
  return CROSSLINKS[book];
}

export function parseChapterNumber(text: string): number | null {
  const m = text.match(/第(\d+)回/);
  return m ? Number(m[1]) : null;
}

export function chaptersFromAppearIn(appearIn: string[] = []): number[] {
  const nums = appearIn.map(parseChapterNumber).filter((n): n is number => n != null);
  return [...new Set(nums)].sort((a, b) => a - b);
}

async function itemIndex(book: string): Promise<Map<string, ItemRef>> {
  const items = await loadBookItems(book);
  return new Map(
    items.map(({ kind, entry }) => [
      entry.data.id,
      { id: entry.data.id, name: entry.data.name, kind },
    ])
  );
}

function resolveIds(ids: string[], index: Map<string, ItemRef>): ItemRef[] {
  const out: ItemRef[] = [];
  const seen = new Set<string>();
  for (const id of ids) {
    const ref = index.get(id);
    if (ref && !seen.has(id)) {
      seen.add(id);
      out.push(ref);
    }
  }
  return out;
}

/** 地点页：相关名物（交叉表 + 实体 location 字段 + 居住者名物） */
export async function relatedItemsForPlace(
  book: string,
  placeId: string,
  occupants: string[] = []
): Promise<ItemRef[]> {
  const cl = crosslinksFor(book);
  if (!cl) return [];

  const index = await itemIndex(book);
  const ids = new Set<string>();

  for (const id of cl.location_items[placeId] ?? []) ids.add(id);

  const all = await loadBookItems(book);
  for (const { entry } of all) {
    const loc = (entry.data as { location?: string }).location;
    if (loc === placeId) ids.add(entry.data.id);
  }

  for (const person of occupants) {
    for (const id of cl.occupant_items[person] ?? []) ids.add(id);
  }

  return resolveIds([...ids], index);
}

/** 名物页：同地其他名物 */
export async function relatedItemsAtSameLocation(
  book: string,
  locationId: string | undefined,
  excludeId: string
): Promise<ItemRef[]> {
  if (!locationId || !crosslinksFor(book)) return [];
  const all = await relatedItemsForPlace(book, locationId, []);
  return all.filter((r) => r.id !== excludeId);
}

export function itemLocationId(entry: ItemEntry['entry']): string | undefined {
  return (entry.data as { location?: string }).location;
}

export async function relatedItemsForChapter(
  book: string,
  itemIds: string[]
): Promise<ItemRef[]> {
  const index = await itemIndex(book);
  return resolveIds(itemIds, index);
}

/** 人物页：关联名物（crosslinks occupant_items） */
export async function relatedItemsForCharacter(
  book: string,
  charId: string
): Promise<ItemRef[]> {
  const cl = crosslinksFor(book);
  if (!cl) return [];
  const index = await itemIndex(book);
  return resolveIds(cl.occupant_items[charId] ?? [], index);
}

/** 人物页：关联交易（crosslinks occupant_transactions，金瓶梅等） */
export async function relatedTransactionsForCharacter(
  book: string,
  charId: string
): Promise<TransactionRef[]> {
  const cl = crosslinksFor(book);
  const ids = cl?.occupant_transactions?.[charId];
  if (!ids?.length) return [];

  const txs = await loadTransactions(book);
  const byId = new Map(txs.map((t) => [t.data.id, t]));

  const out: TransactionRef[] = [];
  for (const id of ids) {
    const tx = byId.get(id);
    if (!tx) continue;
    const d = tx.data;
    out.push({
      id: d.id,
      summary: d.summary ?? d.item_ref ?? d.id,
      chapter: d.chapter,
      amount: d.amount != null ? `${d.amount}${d.currency ?? ''}` : undefined,
    });
  }
  return out.sort((a, b) => a.chapter - b.chapter);
}

export type EventRef = {
  id: string;
  title: string;
  chapters: number[];
  summary?: string;
};

async function milestoneEventsBy(
  book: string,
  predicate: (ids: string[]) => boolean,
  getIds: (data: { characters: string[]; locations: string[] }) => string[],
): Promise<EventRef[]> {
  const events = await loadEvents(book);
  return events
    .filter(
      (e) =>
        e.data.book === book &&
        e.data.subtype === 'milestone' &&
        predicate(getIds(e.data)),
    )
    .map((e) => ({
      id: e.data.id,
      title: e.data.title,
      chapters: e.data.chapters,
      summary: e.data.summary,
    }))
    .sort((a, b) => {
      const ca = a.chapters[0] ?? 999;
      const cb = b.chapters[0] ?? 999;
      if (ca !== cb) return ca - cb;
      return a.id.localeCompare(b.id, 'zh-CN');
    });
}

/** 人物页：参与的大事记节点（saga milestone 反查） */
export async function milestoneEventsForCharacter(
  book: string,
  charId: string,
): Promise<EventRef[]> {
  return milestoneEventsBy(book, (ids) => ids.includes(charId), (d) => d.characters);
}

/** 地点页：发生的大事记节点（saga milestone 反查） */
export async function milestoneEventsForPlace(
  book: string,
  placeId: string,
): Promise<EventRef[]> {
  return milestoneEventsBy(book, (ids) => ids.includes(placeId), (d) => d.locations);
}

/** 读回页：本回交易记录 */
export async function relatedTransactionsForChapter(
  book: string,
  chapter: number
): Promise<TransactionRef[]> {
  const txs = await loadTransactions(book);
  return txs
    .filter((t) => t.data.chapter === chapter)
    .map((t) => {
      const d = t.data;
      return {
        id: d.id,
        summary: d.summary ?? d.item_ref ?? d.id,
        chapter: d.chapter,
        amount: d.amount != null ? `${d.amount}${d.currency ?? ''}` : undefined,
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id, 'zh-CN'));
}
