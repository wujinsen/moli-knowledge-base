import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  KARMA_PHASES,
  type KarmaPhase,
  type ShiKarmaData,
} from '../lib/shiKarma';

interface Props {
  karma: ShiKarmaData;
  bookSlug: string;
}

const HOT = '#c45c26';
const COLD = '#355766';

function syncPhaseUrl(phase: KarmaPhase | null) {
  const url = new URL(window.location.href);
  if (phase) url.searchParams.set('phase', phase);
  else url.searchParams.delete('phase');
  window.history.replaceState({}, '', url.toString());
}

export default function ShiKarmaLoop({ karma, bookSlug }: Props) {
  const [activePhase, setActivePhase] = useState<KarmaPhase | null>(null);

  useEffect(() => {
    const p = new URL(window.location.href).searchParams.get('phase') as KarmaPhase | null;
    if (p && KARMA_PHASES.includes(p)) setActivePhase(p);
  }, []);

  const onPhase = useCallback((phase: KarmaPhase | null) => {
    setActivePhase(phase);
    syncPhaseUrl(phase);
  }, []);

  const total = useMemo(
    () => KARMA_PHASES.reduce((n, p) => n + (karma.by_phase[p]?.length ?? 0), 0),
    [karma],
  );

  return (
    <div className="shi-karma-loop">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted">因果闭环（P3）</span>
        <button
          type="button"
          className={`chip text-xs ${!activePhase ? 'ring-1 ring-[var(--accent)]' : ''}`}
          onClick={() => onPhase(null)}
        >
          全部
        </button>
        {KARMA_PHASES.map((phase) => (
          <button
            key={phase}
            type="button"
            className={`chip text-xs ${activePhase === phase ? 'ring-1 ring-[var(--accent)]' : ''}`}
            onClick={() => onPhase(activePhase === phase ? null : phase)}
          >
            {phase}（{karma.counts[phase] ?? 0}）
          </button>
        ))}
        <span className="text-xs text-muted">{total} 处 phase 标注 · {karma.chains.length} 条示例链</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-5">
        {KARMA_PHASES.map((phase) => {
          const items = karma.by_phase[phase] ?? [];
          const dimmed = activePhase != null && activePhase !== phase;
          return (
            <section
              key={phase}
              className="rounded-xl border p-3 transition"
              style={{
                borderColor: 'var(--line)',
                background: 'var(--paper-2)',
                opacity: dimmed ? 0.45 : 1,
              }}
            >
              <header className="mb-2 flex items-center justify-between gap-1">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--primary)' }}>
                  {phase}
                </h3>
                <span className="text-xs text-muted">{items.length}</span>
              </header>
              <ul className="space-y-1.5">
                {items.slice(0, activePhase === phase ? 20 : 6).map((item) => (
                  <li key={`${phase}-${item.id}`}>
                    <a
                      href={`/${bookSlug}/imagery/${item.id}`}
                      className="block rounded px-1.5 py-1 text-xs hover:bg-white/5"
                      style={{
                        borderLeft: `3px solid ${item.temperature === '热' ? HOT : item.temperature === '冷' ? COLD : 'var(--line)'}`,
                      }}
                      title={item.predicate ? `${item.predicate} → ${item.target ?? ''}` : undefined}
                    >
                      <span className="font-medium" style={{ color: 'var(--ink)' }}>
                        {item.title}
                      </span>
                      {item.chapter != null && (
                        <span className="ml-1 text-muted">· 第{item.chapter}回</span>
                      )}
                    </a>
                  </li>
                ))}
                {items.length > (activePhase === phase ? 20 : 6) && (
                  <li className="text-xs text-muted">+{items.length - (activePhase === phase ? 20 : 6)} …</li>
                )}
              </ul>
            </section>
          );
        })}
      </div>

      {karma.chains.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="text-xs text-muted">闭环链路 →</span>
          {karma.chains.map((c) => (
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
