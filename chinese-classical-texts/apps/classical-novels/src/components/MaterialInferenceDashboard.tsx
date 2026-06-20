import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import { dietChartPalette, kbChartTooltip, KB_CHART } from '../lib/chartTheme';
import {
  DOMAIN_UI,
  MATERIAL_AXIS_COLORS,
  MATERIAL_CHAPTER_JUMP,
  TIER_LABELS,
  type MaterialInferenceData,
} from '../lib/materialInference';

interface Props {
  data: MaterialInferenceData;
  bookSlug: string;
  initialChapter?: number;
}

function axisLabel(data: MaterialInferenceData, id: string): string {
  return data.axes.find((a) => a.id === id)?.label ?? id;
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

export default function MaterialInferenceDashboard({ data, bookSlug, initialChapter }: Props) {
  const domain = data.domain;
  const ui = DOMAIN_UI[domain];
  const colors = MATERIAL_AXIS_COLORS[domain];
  const curveRef = useRef<HTMLDivElement>(null);
  const axisRef = useRef<HTMLDivElement>(null);
  const socialRef = useRef<HTMLDivElement>(null);
  const curveInst = useRef<echarts.ECharts | null>(null);
  const axisInst = useRef<echarts.ECharts | null>(null);
  const socialInst = useRef<echarts.ECharts | null>(null);

  const chapterMax = data.by_chapter.length;
  const milestones = data.saga_milestones ?? [];
  const jumpChapters =
    MATERIAL_CHAPTER_JUMP[bookSlug]?.[domain] ?? [1, Math.floor(chapterMax / 2), chapterMax];
  const palette = useMemo(() => dietChartPalette(bookSlug), [bookSlug]);
  const primaryLabel = data.curve_labels.primary;
  const secondaryLabel = data.curve_labels.secondary;

  const [chapter, setChapter] = useState(initialChapter ?? jumpChapters[1] ?? 38);
  const [focusChar, setFocusChar] = useState<string | null>(null);

  useEffect(() => {
    const urlCh = readUrlChapter();
    if (urlCh && urlCh >= 1 && urlCh <= chapterMax) setChapter(urlCh);
  }, [chapterMax]);

  const onChapter = useCallback((ch: number) => {
    setChapter(ch);
    syncUrlChapter(ch);
  }, []);

  const chRow = data.by_chapter[chapter - 1];

  const curveOption = useMemo((): EChartsOption => {
    const xs = data.by_chapter.map((r) => r.chapter);
    const milestonePoints = milestones.map((m) => ({
      name: m.title,
      coord: [m.chapter, data.by_chapter[m.chapter - 1]?.luxury_smooth ?? 0] as [number, number],
      value: m.title,
      itemStyle: { color: chapter === m.chapter ? palette.milestone : palette.milestoneDim },
    }));

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        ...kbChartTooltip(),
        formatter(params) {
          const rows = Array.isArray(params) ? params : [params];
          const ch = Number(rows[0]?.name);
          const ms = milestones.filter((m) => m.chapter === ch);
          let tip = rows.map((p) => `${p.seriesName}: ${p.value}`).join('<br/>');
          if (ms.length) {
            tip += `<br/><span style="color:${palette.milestone}">大事记：${ms.map((m) => m.title).join(' · ')}</span>`;
          }
          return tip;
        },
      },
      legend: { textStyle: { color: KB_CHART.legend, fontSize: 12 }, top: 0 },
      grid: { left: 52, right: 52, top: 40, bottom: 32 },
      xAxis: {
        type: 'category',
        data: xs,
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11, interval: Math.max(0, Math.floor(chapterMax / 12) - 1) },
        axisLine: { lineStyle: { color: KB_CHART.axisLine } },
      },
      yAxis: [
        {
          type: 'value',
          name: primaryLabel,
          nameTextStyle: { color: KB_CHART.axisName, fontSize: 11 },
          min: 0,
          max: 100,
          axisLabel: { color: KB_CHART.axisLabel, fontSize: 11 },
          splitLine: { lineStyle: { color: KB_CHART.splitLine } },
        },
        {
          type: 'value',
          name: secondaryLabel,
          nameTextStyle: { color: KB_CHART.axisName, fontSize: 11 },
          axisLabel: { color: KB_CHART.axisLabel, fontSize: 11 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: `${primaryLabel}（5回平滑）`,
          type: 'line',
          smooth: true,
          data: data.by_chapter.map((r) => r.luxury_smooth),
          lineStyle: { color: palette.luxury, width: 2 },
          itemStyle: { color: palette.luxurySoft },
          areaStyle: { color: palette.luxuryArea },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: KB_CHART.axisLabel, type: 'dashed', opacity: 0.55 },
            data: data.phases.map((p) => ({ xAxis: p.from, name: p.label })),
          },
          markPoint: milestones.length
            ? { symbol: 'pin', symbolSize: 32, label: { show: false }, data: milestonePoints }
            : undefined,
        },
        {
          name: secondaryLabel,
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          data: data.by_chapter.map((r) => r.balance_smooth),
          lineStyle: { color: palette.balance, width: 2 },
          itemStyle: { color: palette.balance },
        },
      ],
    };
  }, [data, milestones, chapter, chapterMax, palette, primaryLabel, secondaryLabel]);

  const axisOption = useMemo((): EChartsOption => {
    const windowRows = data.by_chapter.filter((r) => Math.abs(r.chapter - chapter) <= 8 && r.entity_count > 0);
    const labels = windowRows.map((r) => `第${r.chapter}回`);
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', ...kbChartTooltip() },
      legend: { textStyle: { color: KB_CHART.legend, fontSize: 11 }, type: 'scroll', top: 0 },
      grid: { left: 48, right: 16, top: 52, bottom: 36 },
      xAxis: {
        type: 'category',
        data: labels,
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11, rotate: 28 },
        axisLine: { lineStyle: { color: KB_CHART.axisLine } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11 },
        splitLine: { lineStyle: { color: KB_CHART.splitLine } },
      },
      series: data.axes.map((a) => ({
        name: a.label,
        type: 'bar',
        stack: domain,
        emphasis: { focus: 'series' },
        itemStyle: { color: colors[a.id] ?? KB_CHART.bronze },
        data: windowRows.map((r) => r.axes[a.id] ?? 0),
      })),
    };
  }, [data, chapter, colors, domain]);

  const socialOption = useMemo((): EChartsOption | null => {
    const segs = data.social?.segments ?? [];
    if (!segs.length) return null;
    const topAxes = data.axes.slice(0, 4);
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', ...kbChartTooltip() },
      legend: { textStyle: { color: KB_CHART.legend, fontSize: 11 }, type: 'scroll', top: 0 },
      grid: { left: 48, right: 16, top: 52, bottom: 36 },
      xAxis: {
        type: 'category',
        data: segs.map((s) => TIER_LABELS[s.id] ?? s.label),
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11 },
        axisLine: { lineStyle: { color: KB_CHART.axisLine } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: KB_CHART.axisLabel, fontSize: 11 },
        splitLine: { lineStyle: { color: KB_CHART.splitLine } },
      },
      series: topAxes.map((a) => ({
        name: a.label,
        type: 'bar',
        stack: 'social',
        itemStyle: { color: colors[a.id] ?? KB_CHART.bronze },
        data: segs.map((s) => s.axes[a.id] ?? 0),
      })),
    };
  }, [data, colors]);

  useEffect(() => {
    const el = curveRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      if (!el.clientHeight) return;
      if (!curveInst.current) curveInst.current = echarts.init(el);
      curveInst.current.setOption(curveOption, true);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      curveInst.current?.dispose();
      curveInst.current = null;
    };
  }, [curveOption]);

  useEffect(() => {
    const el = axisRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      if (!el.clientHeight) return;
      if (!axisInst.current) axisInst.current = echarts.init(el);
      axisInst.current.setOption(axisOption, true);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      axisInst.current?.dispose();
      axisInst.current = null;
    };
  }, [axisOption]);

  useEffect(() => {
    const el = socialRef.current;
    if (!el || !socialOption) return;
    const ro = new ResizeObserver(() => {
      if (!el.clientHeight) return;
      if (!socialInst.current) socialInst.current = echarts.init(el);
      socialInst.current.setOption(socialOption, true);
    });
    ro.observe(el);
    return () => {
      ro.disconnect();
      socialInst.current?.dispose();
      socialInst.current = null;
    };
  }, [socialOption]);

  useEffect(() => {
    curveInst.current?.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: chapter - 1 });
  }, [chapter]);

  const filteredChars = focusChar ? data.characters.filter((c) => c.id === focusChar) : data.characters;

  return (
    <div className="kb-dashboard diet-dashboard">
      <section className="surface diet-panel diet-panel--curve">
        <div className="diet-panel__toolbar">
          <div>
            <h2 className="section-title">{ui.curveTitle}</h2>
            <p className="diet-panel__lead text-sm text-muted">
              {primaryLabel} · {secondaryLabel} · 虚线 = 阶段 · 图钉 = 大事记
            </p>
          </div>
          <div className="diet-chapter-badge" aria-live="polite">
            <span className="diet-chapter-badge__label">选中</span>
            <span className="diet-chapter-badge__value">第 {chapter} 回</span>
            {chRow?.phase && <span className="diet-chapter-badge__phase">{chRow.phase}</span>}
          </div>
        </div>
        <div ref={curveRef} className="diet-chart-panel" />
        <div className="diet-toolbar">
          <div className="diet-toolbar__group">
            <span className="diet-toolbar__label">回目</span>
            <div className="diet-toolbar__chips">
              {jumpChapters.map((n) => (
                <button
                  key={n}
                  type="button"
                  className={`chip chip-md ${chapter === n ? 'is-active' : ''}`}
                  style={chipActive(chapter === n)}
                  onClick={() => onChapter(n)}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          {milestones.length > 0 && (
            <div className="diet-toolbar__group">
              <span className="diet-toolbar__label">大事记</span>
              <div className="diet-toolbar__chips diet-toolbar__chips--scroll">
                {milestones.map((m) => (
                  <a
                    key={m.id}
                    href={m.href}
                    className={`chip chip-md ${chapter === m.chapter ? 'is-active' : ''}`}
                    style={chipActive(chapter === m.chapter)}
                    onClick={(e) => {
                      e.preventDefault();
                      onChapter(m.chapter);
                    }}
                    title={`跳转第${m.chapter}回 · ${m.title}`}
                  >
                    {m.title}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      <div className="diet-dashboard__grid">
        <section className="surface diet-panel">
          <h2 className="section-title">第 {chapter} 回 · 结构轴</h2>
          <p className="diet-panel__lead text-sm text-muted">{chRow?.entity_count ?? 0} {ui.entityLabel}</p>
          <div ref={axisRef} className="diet-chart-panel diet-chart-panel--sm" />
          {chRow && chRow.entities.length > 0 && (
            <div className="diet-toolbar__chips diet-toolbar__chips--wrap">
              {chRow.entities.map((id) => (
                <a key={id} href={`/${bookSlug}/i/${encodeURIComponent(id)}`} className="chip chip-md hover:underline">
                  {id}
                </a>
              ))}
            </div>
          )}
        </section>

        <section className="surface diet-panel">
          <h2 className="section-title">全局结论</h2>
          <ul className="diet-insights">
            {data.global_insights.map((ins) => (
              <li key={ins.title} className="diet-insight-item">
                <strong className="diet-insight-item__title">{ins.title}</strong>
                <p className="diet-insight-item__body">{ins.body}</p>
                {ins.evidence.length > 0 && (
                  <div className="diet-toolbar__chips diet-toolbar__chips--wrap">
                    {ins.evidence.slice(0, 6).map((e) => (
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

      {data.social && (
        <section className="surface diet-panel">
          <h2 className="section-title">{data.social.title}</h2>
          {data.social.inference && <p className="diet-panel__lead text-sm text-muted">{data.social.inference}</p>}
          {socialOption && <div ref={socialRef} className="diet-chart-panel diet-chart-panel--sm" />}
          <div className="diet-social-grid">
            {data.social.segments.map((seg) => (
              <article key={seg.id} className="diet-char-card">
                <div className="diet-char-card__head">
                  <span className="diet-char-card__name">{TIER_LABELS[seg.id] ?? seg.label}</span>
                  <span className="diet-char-card__score diet-char-card__score--ok">{seg.entity_count} 实体</span>
                </div>
                <div className="diet-char-card__bars">
                  {Object.entries(seg.axes)
                    .filter(([, v]) => v > 0)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 4)
                    .map(([k, v]) => {
                      const max = Math.max(...Object.values(seg.axes), 1);
                      return (
                        <div key={k} className="diet-bar-row">
                          <span className="diet-bar-row__label">{axisLabel(data, k)}</span>
                          <div className="diet-bar-track">
                            <div
                              className="diet-bar-fill"
                              style={{ width: `${(v / max) * 100}%`, backgroundColor: colors[k] ?? KB_CHART.bronze }}
                            />
                          </div>
                          <span className="diet-bar-row__val">{v}</span>
                        </div>
                      );
                    })}
                </div>
                {seg.sample_entities.length > 0 && (
                  <div className="diet-toolbar__chips diet-toolbar__chips--wrap">
                    {seg.sample_entities.map((id) => (
                      <a key={id} href={`/${bookSlug}/i/${encodeURIComponent(id)}`} className="chip chip-md hover:underline">
                        {id}
                      </a>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
          {data.social.insights.length > 0 && (
            <ul className="diet-insights diet-insights--compact">
              {data.social.insights.map((ins) => (
                <li key={ins.title} className="diet-insight-item">
                  <strong className="diet-insight-item__title">{ins.title}</strong>
                  <p className="diet-insight-item__body">{ins.body}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <section className="surface diet-panel">
        <h2 className="section-title">{ui.charTitle}</h2>
        <p className="diet-panel__lead text-sm text-muted">{data.inference_note}</p>
        <div className="diet-filter-bar">
          <button
            type="button"
            className={`chip chip-md ${!focusChar ? 'is-active' : ''}`}
            style={chipActive(!focusChar)}
            onClick={() => setFocusChar(null)}
          >
            全部
          </button>
          {data.characters.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`chip chip-md ${focusChar === c.id ? 'is-active' : ''}`}
              style={chipActive(focusChar === c.id)}
              onClick={() => setFocusChar(c.id)}
            >
              {c.name}
            </button>
          ))}
        </div>
        <div className="diet-char-grid">
          {filteredChars.map((c) => (
            <CharacterCard key={c.id} row={c} bookSlug={bookSlug} data={data} colors={colors} />
          ))}
        </div>
      </section>
    </div>
  );
}

function CharacterCard({
  row,
  bookSlug,
  data,
  colors,
}: {
  row: MaterialInferenceData['characters'][0];
  bookSlug: string;
  data: MaterialInferenceData;
  colors: Record<string, string>;
}) {
  const barMax = Math.max(...Object.values(row.axes), 1);

  return (
    <article className="diet-char-card">
      <div className="diet-char-card__head">
        <a href={`/${bookSlug}/c/${encodeURIComponent(row.id)}`} className="diet-char-card__name hover:underline">
          {row.name}
        </a>
        {row.social_tier && (
          <span className="chip chip-mini">{TIER_LABELS[row.social_tier] ?? row.social_tier}</span>
        )}
      </div>
      <div className="diet-char-card__bars">
        {Object.entries(row.axes)
          .filter(([, v]) => v > 0)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 4)
          .map(([k, v]) => (
            <div key={k} className="diet-bar-row">
              <span className="diet-bar-row__label">{data.axes.find((a) => a.id === k)?.label ?? k}</span>
              <div className="diet-bar-track">
                <div
                  className="diet-bar-fill"
                  style={{ width: `${(v / barMax) * 100}%`, backgroundColor: colors[k] ?? KB_CHART.bronze }}
                />
              </div>
              <span className="diet-bar-row__val">{v}</span>
            </div>
          ))}
      </div>
      <p className="diet-char-card__inference">{row.inference}</p>
      {row.risk_tags.length > 0 && (
        <ul className="diet-char-card__risks">
          {row.risk_tags.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      )}
      {row.sample_entities.length > 0 && (
        <div className="diet-toolbar__chips diet-toolbar__chips--wrap">
          {row.sample_entities.map((id) => (
            <a key={id} href={`/${bookSlug}/i/${encodeURIComponent(id)}`} className="chip chip-md hover:underline">
              {id}
            </a>
          ))}
        </div>
      )}
    </article>
  );
}
