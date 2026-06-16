import { getCollection, type CollectionEntry } from 'astro:content';
import transactionsIndex from '../data/transactions_index.json';
import { snapshotEntries, wrapEntry, type SnapshotIndex } from './contentSnapshot';

export type TransactionEntry = CollectionEntry<'transactions'>;

function fromSnapshot(book?: string): TransactionEntry[] {
  const rows = book
    ? snapshotEntries(transactionsIndex as SnapshotIndex<TransactionEntry['data']>, book)
    : Object.values((transactionsIndex as SnapshotIndex<TransactionEntry['data']>).books).flatMap(
        (b) => b.entries,
      );
  return rows.map((data) => {
    const id = `${data.id}.md`;
    return wrapEntry('transactions', id, data) as TransactionEntry;
  });
}

/** 全书或单书交易；content store 为空时回退 transactions_index.json */
export async function loadTransactions(book?: string): Promise<TransactionEntry[]> {
  try {
    const fromStore = await getCollection('transactions');
    if (fromStore.length > 0) {
      return book ? fromStore.filter((t) => t.data.book === book) : fromStore;
    }
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(book);
}
