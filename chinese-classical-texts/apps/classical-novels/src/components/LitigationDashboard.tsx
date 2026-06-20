import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import { kbChartTooltip, KB_CHART } from '../lib/chartTheme';
import {
  LITIGATION_CHAPTER_JUMP,
  LITIGATION_TIER_COLORS,
  LITIGATION_TIER_LABELS,
  litigationChartPalette,
  type LitigationCase,
  type LitigationInferenceData,
} from '../lib/litigationInference';

interface Props {
  data: LitigationInferenceData;
  bookSlug: string;
  initialChapter?: number;
}

function readUrlChapter(): number | null {
  const ch = new URLSearchParams(window.location.search).get('chapter');
  return ch ? Number(ch) : null;
}

function syncUrlChapter(ch: number) {
  const url = new URL(window.location.href);
  url.searchParams.set('chapter', String(ch));
  window.history.replaceState({}, '', url.toString());
}

function chipActive(active: boolean): CSSProperties | undefined {
  return active ? { borderColor: 'var(--accent)', color: 'var(--accent)' } : undefined;
}

function caseById(data: LitigationInferenceData, id: string): LitigationCase | undefined {
  return data.cases.find((c) => c.id === id);
}

export default function LitigationDashboard({ data, bookSlug, initialChapter }: Props) {
  const curveRef = useRef<HTMLDivElement>(null);
  const curveInst = useRef<echarts.ECharts | null>(null);

  const chapterMax = data.by_chapter.length;
  const jumpChapters = LITIGATION_CHAPTER_JUMP[bookSlug] ?? [10, 48];
  const palette = useMemo(() => litigationChartPalette(bookSlug), [bookSlug]);

  const [chapter, setChapter] = useState(initialChapter ?? LITIGATION_CHAPTER_JUMP[bookSlug]?.[4] ?? 48);
  const [focusCase, setFocusCase] = useState<string | null>(null);

  useEffect(() => {
    const urlCh = readUrlChapter();
    if (urlCh && urlCh >= 1 && urlCh <= chapterMax) setChapter(urlCh);
  }, [chapterMax]);

  const onChapter = useCallback((ch: number) => {
    setChapter(ch);
    syncUrlChapter(ch);
    const active = data.by_chapter[ch - 1]?.case_ids ?? [];
    if (active.length === 1) setFocusCase(active[0] ?? null);
  }, [data.by_chapter]);

  const chRow = data.by_chapter[chapter - 1];
  const activeCases = (chRow?.case_ids ?? [])
    .map((id) => caseById(data, id))
    .filter(Boolean) as LitigationCase[];

  const filteredCases = focusCase ? data.cases.filter((c) => c.id === focusCase) : data.cases;

  const curveOption = useMemo((): EChartsOption => {
    const xs = data.by_chapter.map((r) => r.chapter);
    const milestonePoints = data.milestones.map((m) => ({
      name: m.title,
      coord: [m.chapter, data.by_chapter[m.chapter - 1]?.corruption_smooth ?? 0] as [number, number],
      value: m.title,
      itemStyle: {
        color: chapter === m.chapter ? palette.milestone : LITIGATION_TIER_COLORS[m.tier] ?? palette.milestoneDim,
      },
    }));

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        ...kbChartTooltip(),
        formatter(params) {
          const rows = Array.isArray(params) ? params : [params];
          const ch = Number(rows[0]?.name);
          const row = data.by_chapter[ch - 1];
          let tip = rows.map((p) => `${p.seriesName}: ${p.value}`).join('<br/>');
          if (row?.case_ids.length) {
            const names = row.case_ids
              .map((id) => caseById(data, id)?.title)
              .filter(Boolean)
              .join(' · ');
            tip += `<br/><span style="color:${palette.milestone}">案件：${names}</span>`;
          }
          return tip;
        },
      },
      legend: { textStyle: { color: KB_CHART.legend, fontSize: 12 }, top: 0 },
      grid: { left: 52, right: 24, top: 40, bottom: 32 },
      xAxis: {
        type: 'category',
        data: xs,
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11, interval: Math.max(0, Math.floor(chapterMax / 12) - 1) },
        axisLine: { lineStyle: { color: KB_CHART.axisLine } },
      },
      yAxis: {
        type: 'value',
        name: '腐败指数',
        nameTextStyle: { color: KB_CHART.axisName, fontSize: 11 },
        min: 0,
        max: 100,
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11 },
        splitLine: { lineStyle: { color: KB_CHART.splitLine } },
      },
      series: [
        {
          name: '腐败指数（5回平滑）',
          type: 'line',
          smooth: true,
          data: data.by_chapter.map((r) => r.corruption_smooth),
          lineStyle: { color: palette.corruption, width: 2 },
          itemStyle: { color: palette.corruption },
          areaStyle: { color: palette.corruptionArea },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: KB_CHART.axisLabel, type: 'dashed', opacity: 0.55 },
            data: data.phases.map((p) => ({ xAxis: p.from, name: p.label })),
          },
          markPoint: data.milestones.length
            ? { symbol: 'pin', symbolSize: 34, label: { show: false }, data: milestonePoints }
            : undefined,
        },
        {
          name: '当回指数',
          type: 'bar',
          data: data.by_chapter.map((r) => (r.chapter === chapter ? r.corruption_index : 0)),
          itemStyle: { color: `${palette.milestone}88` },
          barWidth: 6,
        },
      ],
    };
  }, [data, chapter, chapterMax, palette]);

  useEffect(() => {
    if (!curveRef.current) return;
    if (!curveInst.current) curveInst.current = echarts.init(curveRef.current);
    curveInst.current.setOption(curveOption, true);
    const ro = new ResizeObserver(() => curveInst.current?.resize());
    ro.observe(curveRef.current);
    return () => ro.disconnect();
  }, [curveOption]);

  return (
    <div className="diet-inference">
      <section className="surface diet-panel">
        <h2 className="section-title">司法腐败曲线</h2>
        <p className="diet-panel__lead text-sm text-muted">
          {data.inference_note} 图钉=案件锚点；峰值为第{data.stats.peak_corruption_chapter}回（指数{' '}
          {data.stats.peak_corruption}）。
        </p>
        <div className="diet-toolbar">
          <span className="diet-toolbar__label">第 {chapter} 回</span>
          <input
            type="range"
            min={1}
            max={chapterMax}
            value={chapter}
            onChange={(e) => onChapter(Number(e.target.value))}
            className="diet-toolbar__slider"
            aria-label="回目"
          />
          <div className="diet-toolbar__chips">
            {jumpChapters.map((ch) => (
              <button
                key={ch}
                type="button"
                className={`chip chip-md ${chapter === ch ? 'is-active' : ''}`}
                style={chipActive(chapter === ch)}
                onClick={() => onChapter(ch)}
              >
                第{ch}回
              </button>
            ))}
          </div>
        </div>
        <div ref={curveRef} className="diet-chart-panel" style={{ height: 320 }} />
        {chRow && (
          <p className="text-sm text-muted mt-2">
            阶段：{chRow.phase || '—'}
            {activeCases.length > 0 && (
              <>
                {' '}
                · 关联案件：
                {activeCases.map((c) => c.title).join('、')}
              </>
            )}
          </p>
        )}
      </section>

      <section className="surface diet-panel">
        <h2 className="section-title">三级司法通关 · 案件轨</h2>
        <div className="diet-filter-bar">
          <button
            type="button"
            className={`chip chip-md ${!focusCase ? 'is-active' : ''}`}
            style={chipActive(!focusCase)}
            onClick={() => setFocusCase(null)}
          >
            全部
          </button>
          {data.cases.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`chip chip-md ${focusCase === c.id ? 'is-active' : ''}`}
              style={{
                ...chipActive(focusCase === c.id),
                borderColor: focusCase === c.id ? LITIGATION_TIER_COLORS[c.tier] : undefined,
              }}
              onClick={() => {
                setFocusCase(c.id);
                onChapter(c.anchor_chapter);
              }}
            >
              {LITIGATION_TIER_LABELS[c.tier] ?? c.tier} · {c.title.replace(/案$/, '')}
            </button>
          ))}
        </div>
        <div className="diet-char-grid">
          {filteredCases.map((c) => (
            <CaseCard key={c.id} row={c} bookSlug={bookSlug} highlight={c.chapters.includes(chapter)} />
          ))}
        </div>
      </section>

      <section className="surface diet-panel">
        <h2 className="section-title">司法关键人物</h2>
        <div className="diet-char-grid">
          {data.officials.map((o) => (
            <article key={o.id} className="diet-char-card">
              <div className="diet-char-card__head">
                <a href={`/${bookSlug}/c/${encodeURIComponent(o.id)}`} className="diet-char-card__name hover:underline">
                  {o.id}
                </a>
                <span className="chip chip-mini">{o.role}</span>
              </div>
              <p className="diet-char-card__inference">{o.inference}</p>
            </article>
          ))}
        </div>
      </section>

      <div className="diet-insights-grid">
        <section className="surface diet-panel">
          <h2 className="section-title">{data.social.title}</h2>
          <p className="diet-panel__lead text-sm text-muted">{data.social.inference}</p>
          <ul className="diet-insights diet-insights--compact">
            {data.social.insights.map((ins) => (
              <li key={ins.title} className="diet-insight-item">
                <strong className="diet-insight-item__title">{ins.title}</strong>
                <p className="diet-insight-item__body">{ins.body}</p>
              </li>
            ))}
          </ul>
        </section>
        <section className="surface diet-panel">
          <h2 className="section-title">全书推演</h2>
          <ul className="diet-insights">
            {data.global_insights.map((ins) => (
              <li key={ins.title} className="diet-insight-item">
                <strong className="diet-insight-item__title">{ins.title}</strong>
                <p className="diet-insight-item__body">{ins.body}</p>
                {ins.evidence.length > 0 && (
                  <div className="diet-toolbar__chips diet-toolbar__chips--wrap">
                    {ins.evidence.map((e) => (
                      <span key={e} className="chip chip-foot chip-mini">
                        {e}
                      </span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

function CaseCard({ row, bookSlug, highlight }: { row: LitigationCase; bookSlug: string; highlight: boolean }) {
  const tierColor = LITIGATION_TIER_COLORS[row.tier] ?? KB_CHART.bronze;

  return (
    <article className="diet-char-card" style={highlight ? { borderColor: tierColor, boxShadow: `0 0 0 1px ${tierColor}44` } : undefined}>
      <div className="diet-char-card__head">
        <span className="diet-char-card__name">{row.title}</span>
        <span className="chip chip-mini" style={{ borderColor: tierColor, color: tierColor }}>
          {LITIGATION_TIER_LABELS[row.tier] ?? row.tier}
        </span>
      </div>
      <p className="text-xs text-muted mb-2">
        锚点第{row.anchor_chapter}回 · 涉及 {row.chapters.join('、')} 回
      </p>
      <p className="diet-char-card__inference">{row.inference}</p>
      <p className="text-sm mt-2" style={{ color: 'var(--ink)' }}>
        <strong>结局：</strong>
        {row.outcome}
      </p>
      {row.bribery.length > 0 && (
        <ul className="diet-char-card__risks">
          {row.bribery.map((b) => (
            <li key={`${b.chapter}-${b.party}-${b.tx_ref ?? 'm'}`}>
              第{b.chapter}回 · {b.party}
              {b.amount_liang != null && ` · ${b.amount_liang}两`}
              {b.note && `（${b.note}）`}
              {b.source === 'transaction' && b.tx_ref && (
                <>
                  {' '}
                  <a href={`/${bookSlug}/silver#${b.tx_ref}`} className="hover:underline" style={{ color: 'var(--accent)' }}>
                    {b.tx_ref}
                  </a>
                </>
              )}
              {b.source === 'manual' && <span className="text-muted"> · 手标</span>}
            </li>
          ))}
        </ul>
      )}
      <div className="diet-toolbar__chips diet-toolbar__chips--wrap mt-2">
        <a href={`/${bookSlug}/read/cihua/${row.anchor_chapter}`} className="chip chip-md hover:underline">
          读第{row.anchor_chapter}回
        </a>
        {row.links.chain_focus && (
          <a
            href={`/${bookSlug}/chain?focus=${encodeURIComponent(row.links.chain_focus)}`}
            className="chip chip-md hover:underline"
          >
            衰败链 · {row.links.chain_focus}
          </a>
        )}
        {row.links.chain_financial && row.links.chain_financial !== row.links.chain_focus && (
          <a
            href={`/${bookSlug}/chain?focus=${encodeURIComponent(row.links.chain_financial)}`}
            className="chip chip-md hover:underline"
          >
            白银节点 · {row.links.chain_financial}
          </a>
        )}
        {row.links.saga && (
          <a href={`/${bookSlug}/saga#${row.links.saga}`} className="chip chip-md hover:underline">
            大事记
          </a>
        )}
        {(row.links.silver_tx ?? []).map((tid) => (
          <a key={tid} href={`/${bookSlug}/silver#${tid}`} className="chip chip-md hover:underline">
            {tid}
          </a>
        ))}
        {row.links.silver && !row.links.silver_tx?.length && (
          <a href={`/${bookSlug}/silver?chapter=${row.anchor_chapter}`} className="chip chip-md hover:underline">
            白银流
          </a>
        )}
      </div>
    </article>
  );
}
