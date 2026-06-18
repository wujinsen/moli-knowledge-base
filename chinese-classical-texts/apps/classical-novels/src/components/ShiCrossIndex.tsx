import { useEffect, useMemo, useState } from 'react';
import { readChapterPath } from '../lib/editions';
import { KARMA_PHASES, type KarmaPhase } from '../lib/shiKarma';
import type { ShiCrossIndex } from '../lib/shiIndex';
import { subtypeLabel } from '../lib/shiIndex';

interface Props {
  index: ShiCrossIndex;
  bookSlug: string;
  bookName: string;
}

type Mode = 'chapter' | 'character';

function matchQuery(text: string, q: string): boolean {
  if (!q) return true;
  return text.toLowerCase().includes(q.toLowerCase());
}

function rowMatches(row: { title: string; id: string; characters: string[]; phases?: string[] }, q: string): boolean {
  if (!q) return true;
  const hay = [row.title, row.id, ...row.characters, ...(row.phases ?? [])].join(' ');
  return matchQuery(hay, q);
}

function rowInPhase(row: { phases?: string[] }, phase: KarmaPhase | null): boolean {
  if (!phase) return true;
  return row.phases?.includes(phase) ?? false;
}

function defaultExpandedKeys(index: ShiCrossIndex, mode: Mode): Set<string> {
  const keys = new Set<string>();
  const groups = mode === 'chapter' ? index.byChapter : index.byCharacter;
  for (const g of groups) {
    const rows = 'rows' in g ? g.rows : [];
    const key = mode === 'chapter' ? `ch-${(g as { chapter: number }).chapter}` : `c-${(g as { character: string }).character}`;
    if (rows.length <= 4) keys.add(key);
  }
  return keys;
}

export default function ShiCrossIndex({ index, bookSlug, bookName }: Props) {
  const isJpm = bookSlug === 'jinpingmei';
  const [mode, setMode] = useState<Mode>('chapter');
  const [query, setQuery] = useState('');
  const [phaseFilter, setPhaseFilter] = useState<KarmaPhase | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(() => defaultExpandedKeys(index, 'chapter'));

  const filtered = useMemo(() => {
    const q = query.trim();
    const matchRow = (row: (typeof index.entries)[0]) =>
      rowMatches(row, q) && rowInPhase(row, phaseFilter);

    if (mode === 'chapter') {
      return index.byChapter
        .map((g) => ({
          ...g,
          rows: g.rows.filter(matchRow),
        }))
        .filter((g) => g.rows.length > 0);
    }
    return index.byCharacter
      .map((g) => ({
        ...g,
        rows: g.rows.filter(matchRow),
      }))
      .filter((g) => g.rows.length > 0 || matchQuery(g.character, q));
  }, [index, mode, query, phaseFilter]);

  const searching = query.trim().length > 0 || phaseFilter !== null;

  useEffect(() => {
    if (!searching) {
      setExpanded(defaultExpandedKeys(index, mode));
      return;
    }
    const keys = new Set<string>();
    if (mode === 'chapter') {
      for (const g of filtered) keys.add(`ch-${g.chapter}`);
    } else {
      for (const g of filtered) keys.add(`c-${g.character}`);
    }
    setExpanded(keys);
  }, [searching, filtered, mode, index]);

  const toggleGroup = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const expandAll = () => {
    const keys = new Set<string>();
    if (mode === 'chapter') {
      for (const g of filtered) keys.add(`ch-${g.chapter}`);
    } else {
      for (const g of filtered) keys.add(`c-${g.character}`);
    }
    setExpanded(keys);
  };

  const collapseAll = () => setExpanded(new Set());

  return (
    <div className="cross-index">
      <div className="cross-index-toolbar">
        <div className="cross-index-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'chapter'}
            className={mode === 'chapter' ? 'is-active' : undefined}
            onClick={() => setMode('chapter')}
          >
            按章回
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'character'}
            className={mode === 'character' ? 'is-active' : undefined}
            onClick={() => setMode('character')}
          >
            按人物
          </button>
        </div>

        {isJpm && (
          <div className="cross-index-phases">
            <button
              type="button"
              className={`chip chip-mini ${!phaseFilter ? 'chip-like' : 'chip-foot'}`}
              onClick={() => setPhaseFilter(null)}
            >
              全阶段
            </button>
            {KARMA_PHASES.map((p) => (
              <button
                key={p}
                type="button"
                className={`chip chip-mini ${phaseFilter === p ? 'chip-like' : 'chip-foot'}`}
                onClick={() => setPhaseFilter(phaseFilter === p ? null : p)}
              >
                {p}
              </button>
            ))}
          </div>
        )}

        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={mode === 'chapter' ? '筛选章回 / 谶纬 / 人物…' : '筛选人物 / 谶纬…'}
          className="cross-index-search"
        />

        <div className="cross-index-actions">
          <button type="button" className="cross-index-link-btn" onClick={expandAll}>
            全部展开
          </button>
          <span className="cross-index-sep">·</span>
          <button type="button" className="cross-index-link-btn" onClick={collapseAll}>
            全部收起
          </button>
        </div>

        <span className="cross-index-stats">
          {index.entries.length} 条 · {index.byChapter.length} 回 · {index.byCharacter.length} 人
        </span>
      </div>

      <div className="cross-index-list">
        {filtered.length === 0 && <p className="cross-index-empty">无匹配项</p>}

        {mode === 'chapter' &&
          filtered.map((g) => {
            const key = `ch-${g.chapter}`;
            const open = expanded.has(key);
            return (
              <details key={g.chapter} className="cross-index-group" open={open}>
                <summary
                  className="cross-index-summary"
                  onClick={(e) => {
                    e.preventDefault();
                    toggleGroup(key);
                  }}
                >
                  <span className="cross-index-chevron" aria-hidden>
                    {open ? '▾' : '▸'}
                  </span>
                  <span className="cross-index-summary-title">第 {g.chapter} 回</span>
                  <span className="chip chip-mini chip-foot">{g.rows.length} 条</span>
                  <a
                    href={readChapterPath(bookSlug, bookName, g.chapter)}
                    className="cross-index-read-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    读回
                  </a>
                </summary>
                <table className="cross-index-table">
                  <tbody>
                    {g.rows.map((row) => (
                      <tr key={row.id}>
                        <td className="cross-index-col-title">
                          <a href={`/${bookSlug}/imagery/${row.id}`}>{row.title}</a>
                        </td>
                        <td className="cross-index-col-tags">
                          <span className="chip chip-mini chip-foot">{subtypeLabel(row.subtype)}</span>
                          {row.hasInference && (
                            <span className="chip chip-mini chip-like">推论</span>
                          )}
                          {row.phases?.map((p) => (
                            <span key={p} className="chip chip-mini">
                              {p}
                            </span>
                          ))}
                        </td>
                        <td className="cross-index-col-links">
                          {row.characters.map((c) => (
                            <a
                              key={c}
                              href={`/${bookSlug}/c/${encodeURIComponent(c)}`}
                              className="chip chip-mini chip-foot"
                            >
                              {c}
                            </a>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            );
          })}

        {mode === 'character' &&
          filtered.map((g) => {
            const key = `c-${g.character}`;
            const open = expanded.has(key);
            return (
              <details key={g.character} className="cross-index-group" open={open}>
                <summary
                  className="cross-index-summary"
                  onClick={(e) => {
                    e.preventDefault();
                    toggleGroup(key);
                  }}
                >
                  <span className="cross-index-chevron" aria-hidden>
                    {open ? '▾' : '▸'}
                  </span>
                  <a
                    href={`/${bookSlug}/c/${encodeURIComponent(g.character)}`}
                    className="cross-index-summary-title cross-index-summary-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {g.character}
                  </a>
                  <span className="chip chip-mini chip-foot">{g.rows.length} 条</span>
                </summary>
                <table className="cross-index-table">
                  <tbody>
                    {g.rows.map((row) => (
                      <tr key={row.id}>
                        <td className="cross-index-col-title">
                          <a href={`/${bookSlug}/imagery/${row.id}`}>{row.title}</a>
                        </td>
                        <td className="cross-index-col-tags">
                          <span className="chip chip-mini chip-foot">{subtypeLabel(row.subtype)}</span>
                          {row.hasInference && (
                            <span className="chip chip-mini chip-like">推论</span>
                          )}
                          {row.phases?.map((p) => (
                            <span key={p} className="chip chip-mini">
                              {p}
                            </span>
                          ))}
                        </td>
                        <td className="cross-index-col-links">
                          {row.chapters.map((ch) => (
                            <a
                              key={ch}
                              href={readChapterPath(bookSlug, bookName, ch)}
                              className="chip chip-mini chip-foot"
                            >
                              第{ch}回
                            </a>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            );
          })}
      </div>
    </div>
  );
}
