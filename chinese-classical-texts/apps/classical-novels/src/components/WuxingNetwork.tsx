import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ELEMENT_COLOR,
  RELATION_COLOR,
  WUXING_ELEMENTS,
  WUXING_RELATIONS,
  type ShiWuxingData,
  type WuxingRelation,
} from '../lib/shiWuxing';

interface Props {
  data: ShiWuxingData;
  bookSlug: string;
  quanshiHref?: string;
}

function syncRelUrl(rel: WuxingRelation | null) {
  const url = new URL(window.location.href);
  if (rel) url.searchParams.set('rel', rel);
  else url.searchParams.delete('rel');
  window.history.replaceState({}, '', url.toString());
}

export default function WuxingNetwork({ data, bookSlug, quanshiHref }: Props) {
  const [activeRel, setActiveRel] = useState<WuxingRelation | null>(null);

  useEffect(() => {
    const r = new URL(window.location.href).searchParams.get('rel') as WuxingRelation | null;
    if (r && WUXING_RELATIONS.includes(r)) setActiveRel(r);
  }, []);

  const onRel = useCallback((rel: WuxingRelation | null) => {
    setActiveRel(rel);
    syncRelUrl(rel);
  }, []);

  const edges = useMemo(
    () => (activeRel ? data.edges.filter((e) => e.predicate === activeRel) : data.edges),
    [data.edges, activeRel],
  );

  return (
    <div className="wuxing-network">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted">五行生克（修心网络）</span>
        <button
          type="button"
          className={`chip text-xs ${!activeRel ? 'ring-1 ring-[var(--accent)]' : ''}`}
          onClick={() => onRel(null)}
        >
          全部
        </button>
        {WUXING_RELATIONS.map((rel) => (
          <button
            key={rel}
            type="button"
            className={`chip text-xs ${activeRel === rel ? 'ring-1 ring-[var(--accent)]' : ''}`}
            onClick={() => onRel(activeRel === rel ? null : rel)}
            style={{ color: RELATION_COLOR[rel] }}
          >
            {rel}（{data.relation_counts[rel] ?? 0}）
          </button>
        ))}
        {quanshiHref && (
          <a href={quanshiHref} className="ml-auto text-xs hover:underline" style={{ color: 'var(--accent)' }}>
            内丹心性说 →
          </a>
        )}
      </div>

      {/* 五行五列：师徒五众配属 */}
      <div className="grid gap-3 sm:grid-cols-5">
        {WUXING_ELEMENTS.map((el) => {
          const nodes = data.by_element[el] ?? [];
          return (
            <section
              key={el}
              className="rounded-xl border p-3"
              style={{ borderColor: 'var(--line)', background: 'var(--paper-2)' }}
            >
              <header className="mb-2 flex items-center gap-2">
                <span
                  className="flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold text-white"
                  style={{ background: ELEMENT_COLOR[el] }}
                >
                  {el}
                </span>
                <span className="text-xs text-muted">{nodes.length}</span>
              </header>
              <ul className="space-y-1.5">
                {nodes.map((n) => (
                  <li key={n.id}>
                    <a
                      href={`/${bookSlug}/imagery/${n.id}`}
                      className="block rounded px-1.5 py-1 text-xs hover:bg-white/5"
                      style={{ borderLeft: `3px solid ${ELEMENT_COLOR[el]}` }}
                    >
                      <span className="font-medium" style={{ color: 'var(--ink)' }}>
                        {n.title}
                      </span>
                      {n.characters.length > 0 && (
                        <span className="ml-1 text-muted">· {n.characters.join('、')}</span>
                      )}
                    </a>
                  </li>
                ))}
                {nodes.length === 0 && <li className="text-xs text-muted">—</li>}
              </ul>
            </section>
          );
        })}
      </div>

      {/* 生克边列表 */}
      <div className="mt-4">
        <h3 className="section-title mb-2 text-sm">生克边（{edges.length}）</h3>
        <ul className="space-y-1.5 text-sm">
          {edges.map((e, i) => (
            <li
              key={`${e.source}-${e.target}-${i}`}
              className="flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg border px-3 py-2"
              style={{ borderColor: 'var(--line)', background: 'var(--paper-2)' }}
            >
              <a
                href={`/${bookSlug}/imagery/${e.source}`}
                className="font-medium hover:underline"
                style={{ color: 'var(--ink)' }}
              >
                {e.sourceTitle}
              </a>
              <span
                className="rounded px-1.5 py-0.5 text-xs font-semibold text-white"
                style={{ background: RELATION_COLOR[e.predicate] }}
              >
                {e.predicate}
              </span>
              <a
                href={`/${bookSlug}/imagery/${e.target}`}
                className="font-medium hover:underline"
                style={{ color: 'var(--ink)' }}
              >
                {e.targetTitle}
              </a>
              {e.chapter != null && <span className="text-xs text-muted">第{e.chapter}回</span>}
              {e.note && <span className="w-full text-xs text-muted">{e.note}</span>}
            </li>
          ))}
          {edges.length === 0 && <li className="text-sm text-muted">无匹配生克边</li>}
        </ul>
      </div>

      {data.chains.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-muted">修心链路 →</span>
          {data.chains.map((c) => (
            <a
              key={c.id}
              href={`/${bookSlug}/shi?chain=${encodeURIComponent(c.id)}`}
              className="chip text-xs hover:underline"
              title={c.summary}
            >
              {c.name}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
