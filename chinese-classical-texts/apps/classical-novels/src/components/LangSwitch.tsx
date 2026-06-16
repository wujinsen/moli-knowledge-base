import { useEffect, useState } from 'react';
import {
  applySiteLocale,
  DEFAULT_LOCALE,
  LOCALE_LABEL,
  readLocale,
  storeLocale,
} from '../lib/i18n/apply';
import type { SiteLocale } from '../lib/i18n/types';

const LOCALES: SiteLocale[] = ['zh', 'en', 'ja'];

export default function LangSwitch() {
  const [locale, setLocale] = useState<SiteLocale>(DEFAULT_LOCALE);

  useEffect(() => {
    const initial = readLocale();
    setLocale(initial);
    applySiteLocale(initial);
  }, []);

  function select(next: SiteLocale) {
    setLocale(next);
    storeLocale(next);
    applySiteLocale(next);
  }

  return (
    <div
      className="lang-switch"
      role="group"
      aria-label={locale === 'zh' ? '语言' : locale === 'ja' ? '言語' : 'Language'}
    >
      {LOCALES.map((code) => (
        <button
          key={code}
          type="button"
          className={`lang-switch-btn${locale === code ? ' is-active' : ''}`}
          aria-pressed={locale === code}
          onClick={() => select(code)}
        >
          {LOCALE_LABEL[code]}
        </button>
      ))}
    </div>
  );
}
