import { messages } from './messages';
import type { BookSlug, SiteLocale } from './types';

export const LOCALE_STORAGE = 'kb-home-locale';
export const DEFAULT_LOCALE: SiteLocale = 'zh';

export const LOCALE_LABEL: Record<SiteLocale, string> = {
  zh: '中',
  en: 'EN',
  ja: '日',
};

export const HTML_LANG: Record<SiteLocale, string> = {
  zh: 'zh-CN',
  en: 'en',
  ja: 'ja',
};

export function getByPath(root: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, part) => {
    if (acc && typeof acc === 'object' && part in (acc as Record<string, unknown>)) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, root);
}

export function modulesLiveLabel(locale: SiteLocale, count: number): string {
  if (locale === 'en') return `${count} module${count === 1 ? '' : 's'} live`;
  if (locale === 'ja') return `${count} モジュール公開中`;
  return `${count} 个模块已上线`;
}

export function startReadingLabel(
  locale: SiteLocale,
  book: BookSlug,
  chapter: number,
  edition?: string,
): string {
  if (locale === 'en') {
    if (book === 'honglou' && edition === 'zhiben') return `Read · Zhiping ch. ${chapter}`;
    if (book === 'jinpingmei' && edition === 'cihua') return `Read · Cihua ed. ch. ${chapter}`;
    return `Read · ch. ${chapter}`;
  }
  if (locale === 'ja') {
    if (book === 'honglou' && edition === 'zhiben') return `読む · 脂本第${chapter}回`;
    if (book === 'jinpingmei' && edition === 'cihua') return `読む · 詞話本第${chapter}回`;
    return `読む · 第${chapter}回`;
  }
  if (book === 'honglou' && edition === 'zhiben') return `开始阅读 · 脂本第${chapter}回`;
  if (book === 'jinpingmei' && edition === 'cihua') return `开始阅读 · 词话本第${chapter}回`;
  return `开始阅读 · 第${chapter}回`;
}

export function readLocale(): SiteLocale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE;
  const raw = localStorage.getItem(LOCALE_STORAGE);
  if (raw === 'en' || raw === 'ja' || raw === 'zh') return raw;
  return DEFAULT_LOCALE;
}

export function storeLocale(locale: SiteLocale): void {
  localStorage.setItem(LOCALE_STORAGE, locale);
}

export function applySiteLocale(locale: SiteLocale): void {
  const copy = messages[locale];
  document.documentElement.lang = HTML_LANG[locale];

  document.querySelectorAll<HTMLElement>('[data-i18n]').forEach((el) => {
    const key = el.dataset.i18n;
    if (!key) return;
    // 只改纯文本节点，避免误清空含子节点的容器
    if (el.childElementCount > 0) return;
    const value = getByPath(copy, key);
    if (typeof value === 'string') el.textContent = value;
  });

  document.querySelectorAll<HTMLElement>('[data-i18n-modules]').forEach((el) => {
    const count = Number(el.dataset.i18nModules ?? '0');
    el.textContent = modulesLiveLabel(locale, count);
  });

  document.querySelectorAll<HTMLElement>('[data-i18n-items-extra]').forEach((el) => {
    const count = el.dataset.i18nItemsExtra ?? '0';
    const prefix = getByPath(copy, 'ui.itemsExtraPrefix');
    const suffix = getByPath(copy, 'ui.itemsExtraSuffix');
    if (typeof prefix === 'string' && typeof suffix === 'string') {
      el.textContent = `${prefix}${count}${suffix}`;
    }
  });

  document.querySelectorAll<HTMLElement>('[data-i18n-fold-hint]').forEach((el) => {
    const scope = el.closest('.catalog-fold-page');
    if (!scope) return;
    const anyOpen = [...scope.querySelectorAll('details.catalog-fold-group')].some(
      (d) => (d as HTMLDetailsElement).open,
    );
    el.hidden = anyOpen;
  });

  document.querySelectorAll<HTMLElement>('[data-i18n-reading]').forEach((el) => {
    const book = el.dataset.i18nBook as BookSlug;
    const chapter = Number(el.dataset.i18nChapter ?? '1');
    const edition = el.dataset.i18nEdition;
    if (book) el.textContent = startReadingLabel(locale, book, chapter, edition);
  });

  const pageTitle = document.body.dataset.pageTitle;
  if (pageTitle) document.title = `${pageTitle} · ${copy.siteTitle}`;
}
