import { getCollection } from 'astro:content';
import chaptersIndex from '../data/chapters_index.json';
import { DEFAULT_EDITION } from './editions';

export interface ChapterLite {
  book: string;
  number: number;
  title: string;
  edition: string;
}

function fromSnapshot(book: string): ChapterLite[] {
  const byEdition = chaptersIndex.books[book as keyof typeof chaptersIndex.books];
  if (!byEdition) return [];
  const out: ChapterLite[] = [];
  for (const [edition, items] of Object.entries(byEdition)) {
    for (const item of items) {
      out.push({
        book,
        number: item.number,
        title: item.title,
        edition,
      });
    }
  }
  return out.sort((a, b) => a.number - b.number || a.edition.localeCompare(b.edition));
}

/** 列出某书全部回目元数据；content store 为空时回退 chapters_index.json */
export async function loadChapterList(book: string): Promise<ChapterLite[]> {
  try {
    const fromStore = await getCollection('chapters');
    if (fromStore.length > 0) {
      return fromStore
        .filter((c) => c.data.book === book)
        .map((c) => ({
          book: c.data.book,
          number: c.data.number,
          title: c.data.title,
          edition: c.data.edition ?? DEFAULT_EDITION,
        }))
        .sort((a, b) => a.number - b.number);
    }
  } catch {
    /* content store unavailable */
  }
  return fromSnapshot(book);
}

export function filterChaptersByEdition(chapters: ChapterLite[], edition: string): ChapterLite[] {
  return chapters.filter((c) => c.edition === edition);
}
