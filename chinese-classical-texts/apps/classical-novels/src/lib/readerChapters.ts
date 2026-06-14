import { getCollection } from 'astro:content';
import {
  DEFAULT_EDITION,
  maxChapterForEdition,
  readChapterPath,
} from './editions';

export type ReaderChapterItem = {
  number: number;
  title: string;
  href: string;
};

/** 去掉空白与常见标点，便于比较回目与摘要是否同一句话 */
function normalizeChapterHeading(text: string): string {
  return text.replace(/[\s\u3000；;，,、·：:\-—]/g, '').trim();
}

/** summary 与 title 实质相同时不重复展示 */
export function shouldShowChapterSummary(title: string, summary?: string | null): boolean {
  if (!summary?.trim()) return false;
  return normalizeChapterHeading(title) !== normalizeChapterHeading(summary);
}

/** 阅读页目录：当前版本下的全部回目 */
export async function listReaderChapters(
  book: string,
  slug: string,
  options?: { edition?: string; bookTotal?: number },
): Promise<ReaderChapterItem[]> {
  const { edition, bookTotal } = options ?? {};
  const all = await getCollection('chapters');

  let list = all.filter((c) => c.data.book === book);
  if (edition) {
    list = list.filter((c) => (c.data.edition ?? DEFAULT_EDITION) === edition);
  }

  const max =
    edition && bookTotal != null
      ? maxChapterForEdition(book, edition, bookTotal)
      : undefined;

  return list
    .filter((c) => max == null || c.data.number <= max)
    .sort((a, b) => a.data.number - b.data.number)
    .map((c) => ({
      number: c.data.number,
      title: c.data.title,
      href: readChapterPath(slug, book, c.data.number, edition),
    }));
}
