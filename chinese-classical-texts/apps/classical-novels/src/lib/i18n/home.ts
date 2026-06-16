/** @deprecated Use imports from ./apply or ./messages */
export {
  DEFAULT_LOCALE as DEFAULT_HOME_LOCALE,
  LOCALE_LABEL as HOME_LOCALE_LABEL,
  LOCALE_STORAGE as HOME_LOCALE_STORAGE,
  HTML_LANG,
  applySiteLocale as applyHomeLocale,
  modulesLiveLabel,
  readLocale as readHomeLocale,
  storeLocale as storeHomeLocale,
} from './apply';

export type { SiteLocale as HomeLocale } from './types';
export { messages as homeCopy } from './messages';

export type BookHomeCopy = {
  essence: string;
  summary: string;
  motifs: [string, string, string];
};

export type HomeCopy = (typeof import('./messages').messages)['zh'];
