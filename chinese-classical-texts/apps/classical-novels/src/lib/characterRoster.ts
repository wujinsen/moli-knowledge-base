/** 图鉴 · 全人物名录（已建页 + 待补建） */

import hlmRoster from '../data/honglou.character_roster.json';
import jpmRoster from '../data/jinpingmei.character_roster.json';
import xyjRoster from '../data/xiyouji.character_roster.json';
import hlmScope from '../data/honglou.character_scope.json';
import xyjScope from '../data/xiyouji.character_scope.json';

export type PendingCharacter = {
  name: string;
  mentions: number;
  chapters: number[];
  appear_in: string[];
  source: string;
  note?: string;
};

export type CharacterScopeLayer = {
  name: string;
  count: number;
  members: string;
  role: string;
};

export type CharacterScopeData = {
  book: string;
  summary: string;
  estimates: { label: string; count: string; note: string }[];
  layers: CharacterScopeLayer[];
  sources: string[];
  topic_slug?: string;
};

const SCOPES: Record<string, CharacterScopeData> = {
  honglou: hlmScope as CharacterScopeData,
  xiyouji: xyjScope as CharacterScopeData,
};

export function loadCharacterScope(bookSlug: string): CharacterScopeData | null {
  return SCOPES[bookSlug] ?? null;
}

export type CharacterRosterData = {
  book: string;
  generated: string;
  paged_count: number;
  pending_count: number;
  pending: PendingCharacter[];
};

const ROSTERS: Record<string, CharacterRosterData> = {
  honglou: hlmRoster as CharacterRosterData,
  jinpingmei: jpmRoster as CharacterRosterData,
  xiyouji: xyjRoster as CharacterRosterData,
};

export function loadCharacterRoster(bookSlug: string): CharacterRosterData | null {
  return ROSTERS[bookSlug] ?? null;
}

export type RosterListItem =
  | { kind: 'paged'; name: string; href: string; summary?: string; entityType: string }
  | { kind: 'pending'; name: string; appear_in: string[]; note?: string; mentions: number };

/** 合并已建页与待补建，按姓名排序 */
export function buildFullRosterList(
  bookSlug: string,
  paged: { data: { id: string; name: string; type: string; summary?: string } }[],
  pending: PendingCharacter[],
): RosterListItem[] {
  const items: RosterListItem[] = [
    ...paged.map((c) => ({
      kind: 'paged' as const,
      name: c.data.name,
      href: `/${bookSlug}/c/${c.data.id}`,
      summary: c.data.summary,
      entityType: c.data.type,
    })),
    ...pending.map((p) => ({
      kind: 'pending' as const,
      name: p.name,
      appear_in: p.appear_in,
      note: p.note,
      mentions: p.mentions,
    })),
  ];
  return items.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
}
