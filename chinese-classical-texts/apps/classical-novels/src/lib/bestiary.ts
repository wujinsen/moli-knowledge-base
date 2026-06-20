/** 图鉴 · 喜好项是否可链至名物页 */

const SLUG_ITEM_PREFIX: Record<string, string> = {
  honglou: 'hongloumeng',
  jinpingmei: 'jinpingmei',
  xiyouji: 'xiyouji',
};

const itemIdModules = import.meta.glob<{ default: string[] }>(
  '../data/*.item_ids.json',
  { eager: true },
);

function loadItemIds(bookSlug: string): Set<string> {
  const prefix = SLUG_ITEM_PREFIX[bookSlug];
  if (!prefix) return new Set();
  const entry = Object.entries(itemIdModules).find(([path]) =>
    path.endsWith(`/${prefix}.item_ids.json`),
  );
  const raw = entry?.[1]?.default ?? entry?.[1];
  return new Set(Array.isArray(raw) ? raw : []);
}

const ITEM_IDS: Record<string, Set<string>> = Object.fromEntries(
  Object.keys(SLUG_ITEM_PREFIX).map((slug) => [slug, loadItemIds(slug)]),
);

export type CardArcNode = {
  chapter?: number;
  stage?: string;
  title?: string;
  note?: string;
};

export type CardCharacterData = {
  结局?: string;
  arc?: CardArcNode[];
  summary?: string;
};

/** 图鉴卡片「结局」：优先 frontmatter，其次 arc 结局节点 */
export function cardOutcome(data: CardCharacterData): string | undefined {
  const explicit = data.结局?.trim();
  if (explicit) return explicit;
  const arc = data.arc ?? [];
  for (let i = arc.length - 1; i >= 0; i -= 1) {
    const node = arc[i];
    if (node.stage === '结局') {
      const title = node.title?.trim();
      const note = node.note?.trim();
      const ch = node.chapter;
      const suffix = ch != null ? `（第${ch}回）` : '';
      if (title) return `${title}${suffix}`;
      if (note) return note.length > 56 ? `${note.slice(0, 56)}…` : note;
    }
  }
  return undefined;
}

export type ChipLinkContext = {
  placeIds?: ReadonlySet<string>;
  characterIds?: ReadonlySet<string>;
  characterAliases?: ReadonlyMap<string, string>;
};

export function likeItemHref(bookSlug: string, like: string): string | null {
  const ids = ITEM_IDS[bookSlug];
  if (!ids?.has(like)) return null;
  return `/${bookSlug}/i/${encodeURIComponent(like)}`;
}

function resolveCharacterHref(
  bookSlug: string,
  label: string,
  ctx?: ChipLinkContext,
): string | null {
  if (!ctx?.characterIds && !ctx?.characterAliases) return null;
  const id = ctx.characterIds?.has(label)
    ? label
    : ctx.characterAliases?.get(label);
  if (!id) return null;
  return `/${bookSlug}/c/${encodeURIComponent(id)}`;
}

/** 图鉴 chip：人物 → 名物 → 地点 */
export function chipHref(
  bookSlug: string,
  label: string,
  ctx?: ChipLinkContext | ReadonlySet<string>,
): string | null {
  const linkCtx: ChipLinkContext | undefined =
    ctx instanceof Set ? { placeIds: ctx } : ctx;
  const char = resolveCharacterHref(bookSlug, label, linkCtx);
  if (char) return char;
  const item = likeItemHref(bookSlug, label);
  if (item) return item;
  if (linkCtx?.placeIds?.has(label)) {
    return `/${bookSlug}/l/${encodeURIComponent(label)}`;
  }
  return null;
}

/** 服饰 / 关键物品等同理链至名物百科 */
export const itemWikiHref = likeItemHref;

/** 人物 frontmatter `关键物品` 的展示标签（按书 slug） */
export function keyItemsLabel(bookSlug: string): string {
  return bookSlug === 'honglou' ? '信物' : '关键物品';
}
