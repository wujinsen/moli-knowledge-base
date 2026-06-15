/** 阅读器：将单段长文还原为章回体段落（不改 chapters/ 原文，仅前端展示） */

/** 段首常见起句（保守列表，避免误拆「十月初一日」「原来…」等） */
const PARA_HEAD_STRONG =
  '话说|却说|且说|再表|单表|却表|按下不表|话休饶舌|话休絮烦|话休|' +
  '说话的|列位看官|按那石上书|单说|' +
  '诗曰|词曰|又诗曰|词云|有诗为证|后人有诗|看官听说|出则既明|' +
  '却说这|原来这|原来这日|原来当日|' +
  '少顷|不多时|时届|自从|其时|' +
  '忽见那|忽听得|忽听那|只听那|但见得';

/** 「一日/这日/那日」仅在其后紧跟逗号时拆段，避免「十月初一日」误切 */
const PARA_HEAD_DAY = '(?<![初十])(?:这日|那日|次日|一日)(?=[,，])';

const PARA_SPLIT_RE = new RegExp(
  `(?<=[。！？；」』”\\"])(?=(?:${PARA_HEAD_STRONG}|${PARA_HEAD_DAY}))`,
  'g',
);

export type ReaderSegmentMode = 'off' | 'para' | 'clause';

export function normalizeSegmentMode(raw: string | null | undefined): ReaderSegmentMode {
  if (raw === 'off' || raw === 'para' || raw === 'clause') return raw;
  if (raw === 'on') return 'clause';
  return 'para';
}

export function splitParagraphText(text: string): string[] {
  const t = text.replace(/\r\n/g, '\n').trim();
  if (!t) return [];

  if (t.includes('\n\n')) {
    const byBlank = t
      .split(/\n\s*\n+/)
      .map((s) => s.replace(/\n+/g, '').trim())
      .filter(Boolean);
    if (byBlank.length > 1) return byBlank;
  }

  const parts = t.split(PARA_SPLIT_RE).map((s) => s.trim()).filter(Boolean);
  return parts.length > 1 ? parts : [t];
}

export function splitTextToClauses(text: string): string[] {
  return text.split(/(?<=[。！？；])/).filter((s) => s.length > 0);
}

export const CHAPTER_BODY_SELECTOR = '.reader-body.reader-content';
export const CHAPTER_TEXT_SELECTOR = `${CHAPTER_BODY_SELECTOR} > p:not(.reader-zhipi-hint)`;

export function extractParagraphPlain(p: HTMLParagraphElement): string {
  return (p.textContent ?? '').replace(/\s+/g, '');
}

export function paragraphNeedsSplit(p: HTMLParagraphElement): boolean {
  if (p.classList.contains('reader-zhipi-hint')) return false;
  if (p.dataset.readerSplit === 'true') return false;
  const plain = extractParagraphPlain(p);
  return plain.length > 400;
}

export function bodyHasMonolithicChapter(body: HTMLElement): boolean {
  const ps = body.querySelectorAll(':scope > p:not(.reader-zhipi-hint)');
  if (ps.length !== 1) return false;
  return paragraphNeedsSplit(ps[0] as HTMLParagraphElement);
}
