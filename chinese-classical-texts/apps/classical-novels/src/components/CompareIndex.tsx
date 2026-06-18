import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  compareChapterPath,
  type CompareIndexData,
  type CompareVariantRow,
} from '../lib/compareIndex';
import { comparePairsFor } from '../lib/editions';

interface Props {
  index: CompareIndexData;
  bookSlug: string;
  chapterCount: number;
  initialPair: string;
}

type FilterMode = 'all' | 'variants';

function syncUrl(pair: string, filter: FilterMode) {
  const url = new URL(window.location.href);
  url.searchParams.set('pair', pair);
  if (filter === 'variants') url.searchParams.set('filter', 'variants');
  else url.searchParams.delete('filter');
  window.history.replaceState({}, '', url.toString());
}

export default function CompareIndex({ index, bookSlug, chapterCount, initialPair }: Props) {
  const pairSlugs = Object.keys(index.pairs);
  const [pairSlug, setPairSlug] = useState(initialPair);
  const [filter, setFilter] = useState<FilterMode>(() => {
    if (typeof window === 'undefined') return 'all';
    return new URL(window.location.href).searchParams.get('filter') === 'variants' ? 'variants' : 'all';
  });

  useEffect(() => {
    const url = new URL(window.location.href);
    const p = url.searchParams.get('pair');
    if (p && index.pairs[p]) setPairSlug(p);
    setFilter(url.searchParams.get('filter') === 'variants' ? 'variants' : 'all');
  }, [index.pairs]);

  const onPair = useCallback(
    (slug: string) => {
      setPairSlug(slug);
      syncUrl(slug, filter);
    },
    [filter],
  );

  const onFilter = useCallback(
    (mode: FilterMode) => {
      setFilter(mode);
      syncUrl(pairSlug, mode);
    },
    [pairSlug],
  );

  const pairMeta = index.pairs[pairSlug] ?? index.pairs[initialPair];
  const variantChapters = new Set(pairMeta?.chapters_with_variants ?? []);

  const rows = useMemo(() => {
    const list: { chapter: number; variants: CompareVariantRow[] }[] = [];
    for (let n = 1; n <= chapterCount; n++) {
      const variants = (index.by_chapter[String(n)] ?? []).filter((v) => v.pairs.includes(pairSlug));
      if (filter === 'variants' && variants.length === 0) continue;
      list.push({ chapter: n, variants });
    }
    return list;
  }, [index, chapterCount, pairSlug, filter]);

  const pairLabels = comparePairsFor(bookSlug);

  return (
    <div className="compare-index">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex rounded-lg border border-white/10 p-0.5 text-sm">
          {pairSlugs.map((slug) => (
            <button
              key={slug}
              type="button"
              className={`rounded-md px-3 py-1.5 transition ${pairSlug === slug ? 'bg-white/15 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
              onClick={() => onPair(slug)}
            >
              {index.pairs[slug]?.label ?? pairLabels[slug]?.label ?? slug}
            </button>
          ))}
        </div>
        <div className="flex rounded-lg border border-white/10 p-0.5 text-sm">
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 transition ${filter === 'all' ? 'bg-white/15 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => onFilter('all')}
          >
            全部回目
          </button>
          <button
            type="button"
            className={`rounded-md px-3 py-1.5 transition ${filter === 'variants' ? 'bg-white/15 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => onFilter('variants')}
          >
            仅异文回（{variantChapters.size}）
          </button>
        </div>
        <span className="text-xs text-slate-500">
          {index.variant_total} 处锚点 · {pairMeta?.variant_count ?? 0} 处本对
        </span>
      </div>

      <div className="surface overflow-hidden">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-muted" style={{ borderBottom: '1.5px solid var(--line)' }}>
              <th className="w-16 px-4 py-2.5 text-left font-normal">回</th>
              <th className="px-4 py-2.5 text-left font-normal">对勘</th>
              <th className="w-32 px-4 py-2.5 text-left font-normal">异文</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ chapter, variants }) => (
              <tr key={chapter} id={`ch-${chapter}`} style={{ borderBottom: '1px solid var(--line)' }}>
                <td className="px-4 py-2 tabular-nums">{chapter}</td>
                <td className="px-4 py-2">
                  <a
                    href={compareChapterPath(bookSlug, pairSlug, chapter)}
                    className="hover:underline"
                    style={{ color: 'var(--accent)' }}
                  >
                    第 {chapter} 回 · {pairMeta?.label}
                  </a>
                </td>
                <td className="px-4 py-2">
                  {variants.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {variants.map((v) => (
                        <a
                          key={v.id}
                          href={`${compareChapterPath(bookSlug, pairSlug, chapter)}?variant=${encodeURIComponent(v.id)}`}
                          className="chip text-xs hover:underline"
                          title={v.summary}
                        >
                          {v.category}
                        </a>
                      ))}
                    </div>
                  ) : (
                    <span>—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
