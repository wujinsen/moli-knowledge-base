import { useMemo, useState } from 'react';
import { readChapterPath } from '../lib/editions';
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

function rowMatches(row: { title: string; id: string; characters: string[] }, q: string): boolean {
  if (!q) return true;
  const hay = [row.title, row.id, ...row.characters].join(' ');
  return matchQuery(hay, q);
}

export default function ShiCrossIndex({ index, bookSlug, bookName }: Props) {
  const [mode, setMode] = useState<Mode>('chapter');
  const [query, setQuery] = useState('');

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
    return index.byCharacter
      .map((g) => ({
        ...g,
        rows: g.rows.filter((r) => rowMatches(r, q)),
      }))
      .filter((g) => g.rows.length > 0 || matchQuery(g.character, q));
  }, [index, mode, query]);

  return (
    <div className="shi-cross-index">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex rounded-lg border border-white/10 p-0.5 text-sm">
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 transition ${mode === 'chapter' ? 'bg-white/15 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setMode('chapter')}
          >
            按章回
          </button>
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 transition ${mode === 'character' ? 'bg-white/15 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setMode('character')}
          >
            按人物
          </button>
        </div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={mode === 'chapter' ? '筛选章回 / 诗词 / 人物…' : '筛选人物 / 诗词…'}
          className="min-w-[12rem] flex-1 rounded-lg border border-white/10 bg-slate-900/50 px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-500"
        />
        <span className="text-xs text-slate-500">
          {index.entries.length} 条 · {index.byChapter.length} 回 · {index.byCharacter.length} 人
        </span>
      </div>

      <div className="space-y-4">
        {filtered.length === 0 && (
          <p className="text-sm text-slate-500">无匹配项</p>
        )}
        {mode === 'chapter' &&
          filtered.map((g) => (
            <section
              key={g.chapter}
              className="rounded-xl border border-white/10 bg-slate-900/40 p-4"
            >
              <div className="mb-3 flex flex-wrap items-baseline gap-2">
                <h3 className="font-semibold text-slate-100">第 {g.chapter} 回</h3>
                <a
                  href={readChapterPath(bookSlug, bookName, g.chapter)}
                  className="text-xs text-amber-200/80 hover:underline"
                >
                  读回 →
                </a>
                <span className="text-xs text-slate-500">{g.rows.length} 条意象</span>
              </div>
              <ul className="space-y-2">
                {g.rows.map((row) => (
                  <li key={row.id} className="flex flex-wrap items-start gap-2 text-sm">
                    <a
                      href={`/${bookSlug}/imagery/${row.id}`}
                      className="font-medium text-amber-100 hover:underline"
                    >
                      {row.title}
                    </a>
                    <span className="rounded px-1.5 py-0.5 text-xs text-slate-400 ring-1 ring-white/10">
                      {subtypeLabel(row.subtype)}
                    </span>
                    {row.hasInference && (
                      <span className="rounded px-1.5 py-0.5 text-xs text-violet-300/90 ring-1 ring-violet-400/30">
                        推论
                      </span>
                    )}
                    {row.characters.map((c) => (
                      <a
                        key={c}
                        href={`/${bookSlug}/c/${encodeURIComponent(c)}`}
                        className="rounded px-1.5 py-0.5 text-xs text-slate-300 ring-1 ring-white/10 hover:bg-white/5"
                      >
                        {c}
                      </a>
                    ))}
                  </li>
                ))}
              </ul>
            </section>
          ))}

        {mode === 'character' &&
          filtered.map((g) => (
            <section
              key={g.character}
              className="rounded-xl border border-white/10 bg-slate-900/40 p-4"
            >
              <div className="mb-3 flex flex-wrap items-baseline gap-2">
                <a
                  href={`/${bookSlug}/c/${encodeURIComponent(g.character)}`}
                  className="font-semibold text-slate-100 hover:underline"
                >
                  {g.character}
                </a>
                <span className="text-xs text-slate-500">{g.rows.length} 条意象</span>
              </div>
              <ul className="space-y-2">
                {g.rows.map((row) => (
                  <li key={row.id} className="flex flex-wrap items-start gap-2 text-sm">
                    <a
                      href={`/${bookSlug}/imagery/${row.id}`}
                      className="font-medium text-amber-100 hover:underline"
                    >
                      {row.title}
                    </a>
                    <span className="rounded px-1.5 py-0.5 text-xs text-slate-400 ring-1 ring-white/10">
                      {subtypeLabel(row.subtype)}
                    </span>
                    {row.chapters.map((ch) => (
                      <a
                        key={ch}
                        href={readChapterPath(bookSlug, bookName, ch)}
                        className="rounded px-1.5 py-0.5 text-xs text-slate-300 ring-1 ring-white/10 hover:bg-white/5"
                      >
                        第{ch}回
                      </a>
                    ))}
                    {row.hasInference && (
                      <span className="rounded px-1.5 py-0.5 text-xs text-violet-300/90 ring-1 ring-violet-400/30">
                        推论
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
      </div>
    </div>
  );
}
