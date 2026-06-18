import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  CAMP_COLOR,
  CAMP_DESC,
  type NanCamp,
  type NanData,
  type NanRow,
} from '../lib/nanIndex';

interface Props {
  data: NanData;
  bookSlug: string;
}

function syncUrl(phase: string | null, camp: string | null) {
  const url = new URL(window.location.href);
  if (phase) url.searchParams.set('phase', phase);
  else url.searchParams.delete('phase');
  if (camp) url.searchParams.set('camp', camp);
  else url.searchParams.delete('camp');
  window.history.replaceState({}, '', url.toString());
}

export default function NanExplorer({ data, bookSlug }: Props) {
  const [phase, setPhase] = useState<string | null>(null);
  const [camp, setCamp] = useState<string | null>(null);

  useEffect(() => {
    const u = new URL(window.location.href).searchParams;
    const p = u.get('phase');
    const c = u.get('camp');
    if (p && data.phases.some((x) => x.key === p)) setPhase(p);
    if (c) setCamp(c);
  }, [data.phases]);

  const update = useCallback((p: string | null, c: string | null) => {
    setPhase(p);
    setCamp(c);
    syncUrl(p, c);
  }, []);

  const campEntries = useMemo(
    () => Object.entries(data.stats.by_camp).sort((a, b) => b[1] - a[1]),
    [data.stats.by_camp],
  );
  const campMax = campEntries.length ? campEntries[0][1] : 1;
  const backed = (data.stats.by_camp['佛门'] ?? 0) + (data.stats.by_camp['道门'] ?? 0) + (data.stats.by_camp['天庭'] ?? 0);
  const unbacked = data.stats.by_camp['打杀自死'] ?? 0;

  const rows: NanRow[] = useMemo(
    () =>
      data.tribulations.filter((r) => {
        if (phase && r.phase !== phase) return false;
        if (camp && !r.monsters.some((m) => m.camp === camp)) return false;
        return true;
      }),
    [data.tribulations, phase, camp],
  );

  return (
    <div className="nan-explorer">
      {/* 靠山统计 */}
      <section className="mb-6">
        <h3 className="section-title mb-1 text-sm">收服者阵营 · 难度统计</h3>
        <p className="mb-3 text-xs text-muted">
          有靠山（佛/道/天）{backed} 例 · 无背景打杀 {unbacked} 例 —— 点名妖魔多有后台，徒手打死的几乎全是野妖。
        </p>
        <div className="space-y-1.5">
          {campEntries.map(([c, n]) => (
            <button
              key={c}
              type="button"
              onClick={() => update(phase, camp === c ? null : c)}
              className={`flex w-full items-center gap-2 rounded-lg px-2 py-1 text-left transition hover:bg-white/5 ${
                camp === c ? 'ring-1 ring-[var(--accent)]' : ''
              }`}
              title={CAMP_DESC[c]}
            >
              <span className="w-16 shrink-0 text-xs font-semibold" style={{ color: CAMP_COLOR[c] }}>
                {c}
              </span>
              <span className="h-3 flex-1 overflow-hidden rounded-full" style={{ background: 'var(--paper-2)' }}>
                <span
                  className="block h-full rounded-full"
                  style={{ width: `${(n / campMax) * 100}%`, background: CAMP_COLOR[c] }}
                />
              </span>
              <span className="w-8 shrink-0 text-right text-xs text-muted">{n}</span>
            </button>
          ))}
        </div>
      </section>

      {/* top 列表 */}
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <TopList title="高频妖魔" items={data.stats.top_monsters} />
        <TopList title="关键法宝" items={data.stats.top_artifacts} />
        <TopList title="险地" items={data.stats.top_locations} />
      </div>

      {/* 过滤器 */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          className={`chip text-xs ${!phase ? 'ring-1 ring-[var(--accent)]' : ''}`}
          onClick={() => update(null, camp)}
        >
          全程（{data.total}）
        </button>
        {data.phases.map((p) => (
          <button
            key={p.key}
            type="button"
            className={`chip text-xs ${phase === p.key ? 'ring-1 ring-[var(--accent)]' : ''}`}
            onClick={() => update(phase === p.key ? null : p.key, camp)}
          >
            {p.label}（{p.count}）
          </button>
        ))}
        {camp && (
          <button type="button" className="text-xs hover:underline" style={{ color: 'var(--accent)' }} onClick={() => update(phase, null)}>
            清除「{camp}」筛选 ✕
          </button>
        )}
      </div>

      {/* 时间轴 */}
      <div className="text-xs text-muted">共 {rows.length} 难</div>
      <ul className="mt-2 space-y-2">
        {rows.map((r) => (
          <li
            key={r.id}
            className="rounded-xl border px-3 py-2.5"
            style={{ borderColor: 'var(--line)', background: 'var(--paper-2)' }}
          >
            <div className="flex flex-wrap items-baseline gap-x-2">
              <span
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                style={{ background: 'var(--primary)' }}
              >
                {r.no}
              </span>
              <a href={`/${bookSlug}/e/${r.id}`} className="font-bold hover:underline" style={{ color: 'var(--primary)' }}>
                {r.title}
                {r.aliases[0] && <span className="text-muted">（{r.aliases[0]}）</span>}
              </a>
              {r.chapters[0] != null && (
                <a href={`/${bookSlug}/read/${r.chapters[0]}`} className="chip chip-mini hover:opacity-80">
                  第{r.chapters[0]}回
                </a>
              )}
              <span className="chip chip-mini">{r.phaseLabel}</span>
            </div>
            {r.summary && <p className="mt-1.5 text-xs leading-snug text-muted">{r.summary}</p>}
            {r.monsters.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {r.monsters.map((m) => (
                  <span
                    key={m.name}
                    className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs"
                    style={{ background: 'var(--paper)', borderLeft: `3px solid ${CAMP_COLOR[m.camp]}` }}
                    title={`${m.camp}${m.收服者 ? ' · 收服者：' + m.收服者 : ''}${m.原型 ? ' · 原型：' + m.原型 : ''}`}
                  >
                    <span style={{ color: 'var(--ink)' }}>{m.name}</span>
                    {m.收服者 && <span className="text-muted">↤{m.收服者}</span>}
                  </span>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function TopList({ title, items }: { title: string; items: [string, number][] }) {
  if (!items.length) return null;
  return (
    <section className="rounded-xl border p-3" style={{ borderColor: 'var(--line)', background: 'var(--paper-2)' }}>
      <h4 className="mb-2 text-xs font-semibold text-muted">{title}</h4>
      <ul className="space-y-1">
        {items.slice(0, 8).map(([name, n]) => (
          <li key={name} className="flex items-center justify-between text-xs">
            <span style={{ color: 'var(--ink)' }}>{name}</span>
            <span className="text-muted">{n}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
