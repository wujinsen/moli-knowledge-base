import { getCollection } from 'astro:content';
import { createMarkdownProcessor } from '@astrojs/markdown-remark';
import { loadBookItems } from './items';
import { loadBookPlaces } from './places';

export type EntityIndex = {
  characters: Set<string>;
  characterAliases: Map<string, string>;
  items: Set<string>;
  locations: Set<string>;
};

const indexCache = new Map<string, Promise<EntityIndex>>();

async function loadEntityIndex(book: string): Promise<EntityIndex> {
  const [characters, items, places] = await Promise.all([
    getCollection('characters', ({ data }) => data.book === book),
    loadBookItems(book),
    loadBookPlaces(book),
  ]);

  const characterIds = new Set<string>();
  const characterAliases = new Map<string, string>();
  for (const c of characters) {
    characterIds.add(c.data.id);
    for (const alias of c.data.aliases) {
      characterAliases.set(alias, c.data.id);
    }
  }

  const itemIds = new Set(items.map(({ entry }) => entry.data.id));
  const locationIds = new Set(places.map((p) => p.data.id));

  return {
    characters: characterIds,
    characterAliases,
    items: itemIds,
    locations: locationIds,
  };
}

export function buildEntityIndex(book: string): Promise<EntityIndex> {
  const cached = indexCache.get(book);
  if (cached) return cached;
  const promise = loadEntityIndex(book);
  indexCache.set(book, promise);
  return promise;
}

function resolveCharacterId(index: EntityIndex, target: string): string | null {
  if (index.characters.has(target)) return target;
  const viaAlias = index.characterAliases.get(target);
  if (viaAlias && index.characters.has(viaAlias)) return viaAlias;
  return null;
}

/** 解析实体 id → 站内路径（人物 / 名物 / 地点） */
export function resolveEntityHref(index: EntityIndex, slug: string, target: string): string | null {
  const trimmed = target.trim();
  if (!trimmed) return null;

  const charId = resolveCharacterId(index, trimmed);
  if (charId) return `/${slug}/c/${encodeURIComponent(charId)}`;

  if (index.items.has(trimmed)) return `/${slug}/i/${encodeURIComponent(trimmed)}`;
  if (index.locations.has(trimmed)) return `/${slug}/l/${encodeURIComponent(trimmed)}`;

  return null;
}

/** 将正文 `[[实体]]` 转为标准 Markdown 链接 */
export function preprocessWikiLinks(body: string | undefined | null, index: EntityIndex, slug: string): string {
  if (!body) return '';
  return body.replace(/\[\[([^\]]+)\]\]/g, (_, raw: string) => {
    const target = raw.trim();
    const href = resolveEntityHref(index, slug, target);
    return href ? `[${target}](${href})` : target;
  });
}

let processorPromise: ReturnType<typeof createMarkdownProcessor> | null = null;

async function getMarkdownProcessor() {
  if (!processorPromise) processorPromise = createMarkdownProcessor();
  return processorPromise;
}

/** 渲染带 wiki 链接的正文 HTML */
export async function renderWikiMarkdownBody(
  body: string,
  index: EntityIndex,
  slug: string,
  fileURL?: URL,
): Promise<string> {
  const processor = await getMarkdownProcessor();
  const md = preprocessWikiLinks(body, index, slug);
  const { code } = await processor.render(md, { fileURL });
  return code;
}

/** 元数据字段是否应尝试链至人物 / 实体 */
export function isEntityMetaLabel(label: string): boolean {
  return ['制造', '持有', '对象', '开方', '穿戴', '食用', '参与者'].includes(label);
}
