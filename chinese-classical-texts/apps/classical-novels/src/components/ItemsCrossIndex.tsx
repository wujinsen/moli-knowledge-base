import { useEffect, useMemo, useState } from 'react';
import { readChapterPath } from '../lib/editions';
import type { ItemsCrossIndex } from '../lib/itemsCrossIndex';
import { kindLabel } from '../lib/itemsCrossIndex';

interface Props {
  index: ItemsCrossIndex;
  bookSlug: string;
  bookName: string;
}

type Mode = 'chapter' | 'character' | 'location';

function matchQuery(text: string, q: string): boolean {
  if (!q) return true;
  return text.toLowerCase().includes(q.toLowerCase());
}

function rowMatches(row: { name: string; id: string; kind: string }, q: string): boolean {
  if (!q) return true;
  const hay = [row.name, row.id, kindLabel(row.kind as Parameters<typeof kindLabel>[0])].join(' ');
  return matchQuery(hay, q);
}

function defaultExpandedKeys(index: ItemsCrossIndex, mode: Mode): Set<string> {
  const keys = new Set<string>();
  const groups =
    mode === 'chapter'
      ? index.byChapter
      : mode === 'character'
        ? index.byCharacter
        : index.byLocation;
  for (const g of groups) {
    const rows = 'rows' in g ? g.rows : [];
    let key: string;
    if (mode === 'chapter') key = `ch-${(g as { chapter: number }).chapter}`;
    else if (mode === 'character') key = `c-${(g as { character: string }).character}`;
    else key = `l-${(g as { location: string }).location}`;
    if (rows.length <= 4) keys.add(key);
  }
  return keys;
}

export default function ItemsCrossIndex({ index, bookSlug, bookName }: Props) {
  const hasLocation = index.byLocation.length > 0;
  const [mode, setMode] = useState<Mode>('chapter');
  const [query, setQuery] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(() => defaultExpandedKeys(index, 'chapter'));

  const filtered = useMemo(() => {
    const q = query.trim();
    if (mode === 'chapter') {
      return index.byChapter
        .map((g) => ({
          ...g,
          rows: g.rows.filter((r) => rowMatches(r, q)),
        }))
        .filter((g) => g.rows.length > 0);
    }
    if (mode === 'character') {
      return index.byCharacter
        .map((g) => ({
          ...g,
          rows: g.rows.filter((r) => rowMatches(r, q)),
        }))
        .filter((g) => g.rows.length > 0 || matchQuery(g.character, q));
    }
    return index.byLocation
      .map((g) => ({
        ...g,
        rows: g.rows.filter((r) => rowMatches(r, q)),
      }))
      .filter((g) => g.rows.length > 0 || matchQuery(g.location, q));
  }, [index, mode, query]);

  const searching = query.trim().length > 0;

  useEffect(() => {
    if (!searching) {
      setExpanded(defaultExpandedKeys(index, mode));
      return;
    }
    const keys = new Set<string>();
    if (mode === 'chapter') {
      for (const g of filtered) keys.add(`ch-${(g as { chapter: number }).chapter}`);
    } else if (mode === 'character') {
      for (const g of filtered) keys.add(`c-${(g as { character: string }).character}`);
    } else {
      for (const g of filtered) keys.add(`l-${(g as { location: string }).location}`);
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
      for (const g of filtered) keys.add(`ch-${(g as { chapter: number }).chapter}`);
    } else if (mode === 'character') {
      for (const g of filtered) keys.add(`c-${(g as { character: string }).character}`);
    } else {
      for (const g of filtered) keys.add(`l-${(g as { location: string }).location}`);
    }
    setExpanded(keys);
  };

  const collapseAll = () => setExpanded(new Set());

  const stats = hasLocation
    ? `${index.entries.length} 条 · ${index.byChapter.length} 回 · ${index.byCharacter.length} 人 · ${index.byLocation.length} 地`
    : `${index.entries.length} 条 · ${index.byChapter.length} 回 · ${index.byCharacter.length} 人`;

  const placeholder =
    mode === 'chapter'
      ? '筛选章回 / 名物…'
      : mode === 'character'
        ? '筛选人物 / 名物…'
        : '筛选地点 / 名物…';

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
          {hasLocation && (
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'location'}
              className={mode === 'location' ? 'is-active' : undefined}
              onClick={() => setMode('location')}
            >
              按地点
            </button>
          )}
        </div>

        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
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

        <span className="cross-index-stats">{stats}</span>
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
                          <a href={`/${bookSlug}/i/${row.id}`}>{row.name}</a>
                        </td>
                        <td className="cross-index-col-tags">
                          <span className="chip chip-mini chip-foot">{kindLabel(row.kind)}</span>
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
                          <a href={`/${bookSlug}/i/${row.id}`}>{row.name}</a>
                        </td>
                        <td className="cross-index-col-tags">
                          <span className="chip chip-mini chip-foot">{kindLabel(row.kind)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            );
          })}

        {mode === 'location' &&
          filtered.map((g) => {
            const key = `l-${g.location}`;
            const open = expanded.has(key);
            return (
              <details key={g.location} className="cross-index-group" open={open}>
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
                    href={`/${bookSlug}/l/${encodeURIComponent(g.location)}`}
                    className="cross-index-summary-title cross-index-summary-link"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {g.location}
                  </a>
                  <span className="chip chip-mini chip-foot">{g.rows.length} 条</span>
                </summary>
                <table className="cross-index-table">
                  <tbody>
                    {g.rows.map((row) => (
                      <tr key={row.id}>
                        <td className="cross-index-col-title">
                          <a href={`/${bookSlug}/i/${row.id}`}>{row.name}</a>
                        </td>
                        <td className="cross-index-col-tags">
                          <span className="chip chip-mini chip-foot">{kindLabel(row.kind)}</span>
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
