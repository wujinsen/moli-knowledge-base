import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  chainEventsForCharacter,
  txChipLabel,
  type ChainIndex,
  type ChainEventRow,
} from '../lib/chainIndex';
import { chainEventHref, silverEventHref, silverTxHref } from '../lib/chain';
import { graphFocusHref } from '../lib/sna';

interface Props {
  index: ChainIndex;
  bookSlug: string;
  readEdition: string;
  features: string[];
}

function subtypeLabel(subtype: string, financialKind?: string): string {
  if (subtype === 'financial') return financialKind ? `白银·${financialKind}` : '白银';
  return '情节';
}

function scrollToFocus(focus: string) {
  const id = focus.startsWith('chain-') ? focus : `chain-${focus}`;
  const el = document.getElementById(id);
  if (!el) return;
  document.querySelectorAll('[data-chain-focus="true"]').forEach((n) => {
    n.removeAttribute('data-chain-focus');
  });
  el.setAttribute('data-chain-focus', 'true');
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function syncFocusUrl(focus: string | null) {
  const url = new URL(window.location.href);
  if (focus) url.searchParams.set('focus', focus);
  else url.searchParams.delete('focus');
  window.history.replaceState({}, '', url.toString());
}

function EventCard({
  ev,
  idx,
  bookSlug,
  readEdition,
  features,
  txChips,
  onFocus,
  focused,
}: {
  ev: ChainEventRow;
  idx: number;
  bookSlug: string;
  readEdition: string;
  features: string[];
  txChips: ChainIndex['tx_chips'];
  onFocus: (id: string) => void;
  focused: boolean;
}) {
  const ml = ev.module_links;
  const amount = ev.amount_liang != null ? `${ev.amount_liang}两` : null;

  return (
    <article
      className="timeline-item surface cursor-pointer transition"
      id={`chain-${ev.id}`}
      data-chain-focus={focused ? 'true' : undefined}
      onClick={() => onFocus(ev.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onFocus(ev.id);
        }
      }}
      role="button"
      tabIndex={0}
      style={
        focused
          ? {
              outline: '2px solid color-mix(in srgb, var(--accent) 55%, transparent)',
              outlineOffset: '2px',
              background: 'color-mix(in srgb, var(--accent) 6%, var(--surface))',
            }
          : undefined
      }
    >
      <div className="timeline-marker">
        <span className="timeline-no">{idx + 1}</span>
      </div>
      <div className="timeline-body min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h2 className="brand text-xl" style={{ color: 'var(--primary)' }}>
            <a
              href={`/${bookSlug}/e/${ev.id}`}
              className="hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {ev.title}
            </a>
          </h2>
          <span className="chip text-xs">{subtypeLabel(ev.subtype, ev.financial_kind)}</span>
          {amount && <span className="chip text-xs">{amount}</span>}
          <span className="text-xs text-muted">{ev.phase_label}</span>
        </div>
        {ev.summary && (
          <p className="mt-1 text-sm leading-snug text-muted">{ev.summary}</p>
        )}
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <a
            href={`/${bookSlug}/read/${readEdition}/${ev.chapter}`}
            className="chip hover:opacity-80"
            onClick={(e) => e.stopPropagation()}
          >
            第{ev.chapter}回
          </a>
          {ev.characters.slice(0, 4).map((c) => (
            <a
              key={c}
              href={`/${bookSlug}/c/${c}`}
              className="chip hover:opacity-80"
              onClick={(e) => e.stopPropagation()}
            >
              {c}
            </a>
          ))}
          {ev.locations.map((l) => (
            <a
              key={l}
              href={`/${bookSlug}/l/${l}`}
              className="chip hover:opacity-80"
              onClick={(e) => e.stopPropagation()}
            >
              {l}
            </a>
          ))}
        </div>

        {ev.transaction_refs.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="chip chip-mini text-muted">交易芯片</span>
            {ev.transaction_refs.map((tid) => {
              const chip = txChips[tid];
              return (
                <a
                  key={tid}
                  href={silverTxHref(bookSlug, tid)}
                  className="chip hover:opacity-80"
                  title={chip?.summary || tid}
                  onClick={(e) => e.stopPropagation()}
                >
                  {txChipLabel(chip, tid)}
                </a>
              );
            })}
          </div>
        )}

        {(ml.has_silver || ml.has_sna || ml.graph_focus) && (
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="chip chip-mini">联动</span>
            {ml.has_silver && (
              <a
                href={silverEventHref(bookSlug, ev.id)}
                className="chip hover:opacity-80"
                style={{ color: 'var(--accent)' }}
                onClick={(e) => e.stopPropagation()}
              >
                白银流 · {ev.transaction_refs.length} 笔
              </a>
            )}
            {ml.graph_focus && features.includes('graph') && (
              <a
                href={graphFocusHref(bookSlug, ml.graph_focus!)}
                className="chip hover:opacity-80"
                style={{ color: 'var(--accent)' }}
                onClick={(e) => e.stopPropagation()}
              >
                图谱 · {ml.graph_focus}
              </a>
            )}
            {ml.has_sna && ml.graph_focus && features.includes('sna') && (
              <a
                href={`/${bookSlug}/sna?focus=${encodeURIComponent(ml.graph_focus!)}`}
                className="chip hover:opacity-80"
                style={{ color: 'var(--accent)' }}
                onClick={(e) => e.stopPropagation()}
              >
                SNA
              </a>
            )}
          </div>
        )}

        <div className="mt-2 flex gap-3 text-xs" style={{ color: 'var(--accent)' }}>
          {ev.prev && (
            <a
              href={`/${bookSlug}/e/${ev.prev}`}
              className="hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              ← 上一节点
            </a>
          )}
          {ev.next && (
            <a
              href={`/${bookSlug}/e/${ev.next}`}
              className="hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              下一节点 →
            </a>
          )}
        </div>
      </div>
    </article>
  );
}

export default function ChainTimeline({ index, bookSlug, readEdition, features }: Props) {
  const [phaseKey, setPhaseKey] = useState<string | null>(null);
  const [focusId, setFocusId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!phaseKey) return index.events;
    const ph = index.phases.find((p) => p.key === phaseKey);
    if (!ph) return index.events;
    const [lo, hi] = ph.range;
    return index.events.filter((e) => e.chapter >= lo && e.chapter <= hi);
  }, [index, phaseKey]);

  const applyFocus = useCallback((id: string | null) => {
    setFocusId(id);
    syncFocusUrl(id);
    if (id) scrollToFocus(id);
  }, []);

  useEffect(() => {
    const fromUrl = () => {
      const params = new URLSearchParams(window.location.search);
      const q = params.get('focus');
      const hash = window.location.hash.replace(/^#chain-/, '').replace(/^#/, '');
      const id = q || hash || null;
      if (id && index.events.some((e) => e.id === id)) {
        setFocusId(id);
        window.setTimeout(() => scrollToFocus(id), 80);
      }
    };
    fromUrl();
    window.addEventListener('hashchange', fromUrl);
    window.addEventListener('popstate', fromUrl);
    return () => {
      window.removeEventListener('hashchange', fromUrl);
      window.removeEventListener('popstate', fromUrl);
    };
  }, [index.events]);

  return (
    <div className="chain-timeline">
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          className={`chip text-xs transition ${!phaseKey ? 'ring-2 ring-[var(--accent)]' : ''}`}
          onClick={() => setPhaseKey(null)}
        >
          全部（{index.event_count}）
        </button>
        {index.phases.map((p) => (
          <button
            key={p.key}
            type="button"
            className={`chip text-xs transition ${phaseKey === p.key ? 'ring-2 ring-[var(--accent)]' : ''}`}
            onClick={() => setPhaseKey(phaseKey === p.key ? null : p.key)}
          >
            {p.label} · 第{p.range[0]}–{p.range[1]}回（{p.count}）
          </button>
        ))}
      </div>

      {focusId && (
        <p className="mb-3 text-xs" style={{ color: 'var(--accent)' }}>
          高亮节点{' '}
          <a href={chainEventHref(bookSlug, focusId)} className="hover:underline">
            {focusId}
          </a>
          {' · '}
          <button type="button" className="hover:underline" onClick={() => applyFocus(null)}>
            清除
          </button>
        </p>
      )}

      <div className="tribulation-timeline mb-10">
        {filtered.map((ev, i) => (
          <EventCard
            key={ev.id}
            ev={ev}
            idx={i}
            bookSlug={bookSlug}
            readEdition={readEdition}
            features={features}
            txChips={index.tx_chips}
            onFocus={applyFocus}
            focused={focusId === ev.id}
          />
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-muted">该阶段暂无节点</p>
        )}
      </div>
    </div>
  );
}

export { chainEventsForCharacter };
