/** 阅读版本与 URL（外层选版，章内不再切换） */

export const DEFAULT_EDITION = '程高本';

export const EDITION_SHORT: Record<string, string> = {
  程高本: '程高本',
  脂砚斋本: '脂本',
  词话本: '词话本',
  崇祯本: '崇祯本',
  张竹坡评本: '竹坡本',
  世德堂本: '世德堂本',
};

/** 版本名 → URL 段 */
export const EDITION_SLUG: Record<string, string> = {
  程高本: 'chenggao',
  脂砚斋本: 'zhiben',
  词话本: 'cihua',
  崇祯本: 'chongzhen',
  张竹坡评本: 'zhupo',
  世德堂本: 'shide',
};

export const SLUG_TO_EDITION: Record<string, string> = Object.fromEntries(
  Object.entries(EDITION_SLUG).map(([name, slug]) => [slug, name]),
);

export const ZHIBEN_MAX = 80;

export function readerEditions(book: string): string[] {
  if (book === '红楼梦') return ['脂砚斋本', '程高本'];
  if (book === '金瓶梅') return ['词话本', '崇祯本', '张竹坡评本'];
  return [DEFAULT_EDITION];
}

export function hasMultipleEditions(book: string): boolean {
  return readerEditions(book).length > 1;
}

export function editionLabel(edition: string): string {
  return EDITION_SHORT[edition] ?? edition;
}

export function editionSlug(edition: string): string {
  return EDITION_SLUG[edition] ?? 'default';
}

export function editionFromSlug(slug: string): string | undefined {
  return SLUG_TO_EDITION[slug];
}

export function defaultEditionForBook(book: string): string {
  return readerEditions(book)[0] ?? DEFAULT_EDITION;
}

/** 某一回应使用的默认版本（脂本仅前 80 回） */
export function defaultEditionForChapter(book: string, chapter: number): string {
  if (book === '红楼梦' && chapter > ZHIBEN_MAX) return '程高本';
  return defaultEditionForBook(book);
}

export function defaultEditionSlug(book: string): string {
  return editionSlug(defaultEditionForBook(book));
}

/** 阅读目录页 */
export function readIndexPath(slug: string, book: string, edition?: string): string {
  if (hasMultipleEditions(book)) {
    const ed = edition ?? defaultEditionForBook(book);
    return `/${slug}/read/${editionSlug(ed)}`;
  }
  return `/${slug}`;
}

/** 某一回阅读页 */
export function readChapterPath(
  slug: string,
  book: string,
  chapter: number,
  edition?: string,
): string {
  if (hasMultipleEditions(book)) {
    const ed = edition ?? defaultEditionForChapter(book, chapter);
    return `/${slug}/read/${editionSlug(ed)}/${chapter}`;
  }
  return `/${slug}/read/${chapter}`;
}

export function maxChapterForEdition(book: string, edition: string, bookTotal: number): number {
  if (edition === '脂砚斋本' && book === '红楼梦') return ZHIBEN_MAX;
  return bookTotal;
}

export function editionAvailable(book: string, chapter: number, edition: string): boolean {
  if (edition === '脂砚斋本' && book === '红楼梦') return chapter <= ZHIBEN_MAX;
  return readerEditions(book).includes(edition);
}

/** 版本 Tab 副标题（书目 / 阅读外层） */
export function editionTabMeta(book: string, edition: string): string | undefined {
  if (book === '红楼梦') {
    if (edition === '脂砚斋本') return '前 80 回 · 含脂批 · 默认';
    if (edition === '程高本') return '120 回 · 通行本';
  }
  if (book === '金瓶梅') {
    if (edition === '词话本') return '100 回 · 最接近原貌 · 默认';
    if (edition === '崇祯本') return '100 回 · 文学加工版';
    if (edition === '张竹坡评本') return '100 回 · 含批语 · 影响最大';
  }
  return undefined;
}
