import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import {
  characterHref,
  filterMetrics,
  graphFocusHref,
  proximityLabel,
  rankLabel,
  silverHref,
  snaFocusHref,
  type SnaData,
  type SnaMetric,
} from '../lib/sna';
import { chainEventsForCharacter } from '../lib/chainIndex';
import { chainEventHref } from '../lib/chain';

interface Props {
  data: SnaData;
  bookSlug: string;
}

type MetricMode = 'betweenness' | 'degree';

const BANGXIAN = '帮闲圈';

function syncFocusUrl(id: string | null) {
  const url = new URL(window.location.href);
  if (id) url.searchParams.set('focus', id);
  else url.searchParams.delete('focus');
  window.history.replaceState({}, '', url.toString());
}

function metricValue(m: SnaMetric, mode: MetricMode): number {
  return mode === 'betweenness' ? m.betweenness : m.degree;
}

function metricRank(m: SnaMetric, mode: MetricMode): number {
  return mode === 'betweenness' ? (m.betweenness_rank ?? 0) : (m.degree_rank ?? 0);
}

export default function SnaDashboard({ data, bookSlug }: Props) {
  const barRef = useRef<HTMLDivElement>(null);
  const scatterRef = useRef<HTMLDivElement>(null);
  const barInst = useRef<echarts.ECharts | null>(null);
  const scatterInst = useRef<echarts.ECharts | null>(null);

  const [faction, setFaction] = useState<string | undefined>(undefined);
  const [metricMode, setMetricMode] = useState<MetricMode>('betweenness');
  const [focusId, setFocusId] = useState<string | undefined>(undefined);

  useEffect(() => {
    const apply = () => {
      const q = new URLSearchParams(window.location.search).get('focus');
      setFocusId(q ?? undefined);
      if (q) {
        window.setTimeout(() => {
          document.querySelector('[data-sna-focus="true"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 120);
      }
    };
    apply();
    window.addEventListener('popstate', apply);
    return () => window.removeEventListener('popstate', apply);
  }, []);

  const applyFocus = useCallback((id: string) => {
    setFocusId(id);
    syncFocusUrl(id);
  }, []);

  const rows = useMemo(() => filterMetrics(data, faction).slice(0, 20), [data, faction]);
  const factionKeys = useMemo(
    () => Object.keys(data.factions ?? {}).sort((a, b) => a.localeCompare(b, 'zh')),
    [data.factions],
  );

  const barOption = useMemo((): EChartsOption => {
    const top = [...rows]
      .sort((a, b) => metricValue(b, metricMode) - metricValue(a, metricMode))
      .slice(0, 10);
    const label = metricMode === 'betweenness' ? '介数中心性' : '度中心性';
    return {
      backgroundColor: 'transparent',
      grid: { left: 72, right: 24, top: 8, bottom: 24 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 14 },
        formatter: (params: { dataIndex?: number }[]) => {
          const m = top[(params[0]?.dataIndex ?? 0)];
          if (!m) return '';
          return `${m.id}<br/>${label}：${metricValue(m, metricMode)}<br/>度 ${m.degree} · 介数 ${m.betweenness.toFixed(4)}<br/><span style="opacity:0.7">点击跳转图谱</span>`;
        },
      },
      xAxis: {
        type: 'value',
        name: metricMode === 'betweenness' ? '介数' : '度',
        nameTextStyle: { color: '#5c6359', fontSize: 12 },
        axisLabel: { color: '#5c6359', fontSize: 14 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.15)' } },
      },
      yAxis: {
        type: 'category',
        data: top.map((m) => m.id).reverse(),
        axisLabel: { color: '#1f261f', fontFamily: '"Noto Serif SC", serif', fontSize: 13 },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: top.map((m) => metricValue(m, metricMode)).reverse(),
          itemStyle: { color: metricMode === 'betweenness' ? '#607a67' : '#9c8450', borderRadius: [0, 4, 4, 0] },
          barMaxWidth: 18,
        },
      ],
    };
  }, [rows, metricMode]);

  const scatterOption = useMemo((): EChartsOption => {
    const pts = rows.slice(0, 40);
    const facColors: Record<string, string> = {};
    let fi = 0;
    const palette = ['#607a67', '#9c8450', '#74332c', '#5c6359', '#8a6532', '#6c8576'];
    return {
      backgroundColor: 'transparent',
      grid: { left: 48, right: 16, top: 16, bottom: 36 },
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
        formatter: (p: { data?: number[]; name?: string }) => {
          const m = pts.find((x) => x.id === p.name);
          if (!m) return p.name ?? '';
          return `${m.id}<br/>度 ${m.degree} · 介数 ${m.betweenness.toFixed(4)}<br/>${m.faction ?? ''}`;
        },
      },
      xAxis: {
        type: 'value',
        name: '度',
        nameTextStyle: { color: '#5c6359', fontSize: 12 },
        axisLabel: { color: '#5c6359' },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.12)' } },
      },
      yAxis: {
        type: 'value',
        name: '介数',
        nameTextStyle: { color: '#5c6359', fontSize: 12 },
        axisLabel: { color: '#5c6359' },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.12)' } },
      },
      series: [
        {
          type: 'scatter',
          symbolSize: (val: number[]) => 8 + Math.sqrt(val[0] ?? 0) * 2,
          data: pts.map((m) => {
            const fac = m.faction ?? '—';
            if (!facColors[fac]) facColors[fac] = palette[fi++ % palette.length]!;
            return {
              name: m.id,
              value: [m.degree, m.betweenness],
              itemStyle: { color: facColors[fac] },
            };
          }),
        },
      ],
    };
  }, [rows]);

  const bindBarClick = useCallback(() => {
    barInst.current?.off('click');
    barInst.current?.on('click', (p: { name?: string }) => {
      if (p.name) {
        applyFocus(p.name);
        window.open(graphFocusHref(bookSlug, p.name), '_self');
      }
    });
  }, [applyFocus, bookSlug]);

  const bindScatterClick = useCallback(() => {
    scatterInst.current?.off('click');
    scatterInst.current?.on('click', (p: { name?: string }) => {
      if (p.name) applyFocus(p.name);
    });
  }, [applyFocus]);

  const renderCharts = useCallback(() => {
    if (barRef.current) {
      if (!barInst.current) barInst.current = echarts.init(barRef.current);
      barInst.current.setOption(barOption, true);
      bindBarClick();
    }
    if (scatterRef.current) {
      if (!scatterInst.current) scatterInst.current = echarts.init(scatterRef.current);
      scatterInst.current.setOption(scatterOption, true);
      bindScatterClick();
    }
  }, [barOption, scatterOption, bindBarClick, bindScatterClick]);

  useEffect(() => {
    renderCharts();
    const ro = new ResizeObserver(() => {
      barInst.current?.resize();
      scatterInst.current?.resize();
    });
    if (barRef.current) ro.observe(barRef.current);
    if (scatterRef.current) ro.observe(scatterRef.current);
    return () => {
      ro.disconnect();
      barInst.current?.dispose();
      scatterInst.current?.dispose();
      barInst.current = null;
      scatterInst.current = null;
    };
  }, [renderCharts]);

  const bangxian = data.bangxian_hubs ?? [];
  const degreeHubs = data.degree_hubs ?? [];
  const silverLinks = data.silver_links ?? {};

  return (
    <div className="sna-dashboard space-y-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {data.hubs.slice(0, 3).map((id, i) => (
          <a
            key={`bc-${id}`}
            href={graphFocusHref(bookSlug, id)}
            className="rounded-xl border px-4 py-3 transition hover:opacity-90"
            style={{ borderColor: 'var(--line)', background: 'var(--surface)' }}
            onClick={() => applyFocus(id)}
          >
            <div className="text-xs text-muted">介数 Top {i + 1}</div>
            <div className="brand mt-1 text-xl" style={{ color: 'var(--primary)' }}>{id}</div>
          </a>
        ))}
      </div>

      {degreeHubs.length > 0 && (
        <div className="flex flex-wrap gap-2 text-sm text-muted">
          <span className="chip text-xs">度中心 Top</span>
          {degreeHubs.slice(0, 5).map((id) => (
            <a
              key={`deg-${id}`}
              href={graphFocusHref(bookSlug, id)}
              className="chip text-xs hover:underline"
              style={{ color: 'var(--accent)' }}
              onClick={() => applyFocus(id)}
            >
              {id}
            </a>
          ))}
        </div>
      )}

      {bangxian.length > 0 && (
        <div className="surface px-4 py-3 text-sm text-muted">
          <span className="chip text-xs">{BANGXIAN}</span>
          <span className="ml-2" style={{ color: 'var(--ink)' }}>
            派系内介数前列：
            {bangxian.slice(0, 5).map((id, i) => (
              <span key={id}>
                {i > 0 && ' · '}
                <a href={graphFocusHref(bookSlug, id)} className="hover:underline" style={{ color: 'var(--accent)' }}>
                  {id}
                </a>
              </span>
            ))}
          </span>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={`chip ${!faction ? 'ring-1' : ''}`}
          style={{ borderColor: !faction ? 'var(--accent)' : undefined }}
          onClick={() => setFaction(undefined)}
        >
          全部派系
        </button>
        {factionKeys.map((f) => (
          <button
            key={f}
            type="button"
            className={`chip ${faction === f ? 'ring-1' : ''}`}
            style={{ borderColor: faction === f ? 'var(--accent)' : undefined }}
            onClick={() => setFaction(f === faction ? undefined : f)}
          >
            {f}
            {data.factions?.[f] && ` (${data.factions[f].count})`}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={`chip text-xs ${metricMode === 'betweenness' ? 'ring-2 ring-[var(--accent)]' : ''}`}
          onClick={() => setMetricMode('betweenness')}
        >
          介数中心性
        </button>
        <button
          type="button"
          className={`chip text-xs ${metricMode === 'degree' ? 'ring-2 ring-[var(--accent)]' : ''}`}
          onClick={() => setMetricMode('degree')}
        >
          度中心性
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="section-title mb-2 text-sm">Top 10 · {metricMode === 'betweenness' ? '介数' : '度'}</h3>
          <div
            ref={barRef}
            className="w-full rounded-xl border"
            style={{
              height: Math.max(220, Math.min(10, rows.length) * 28 + 40),
              borderColor: 'var(--line)',
              background: 'color-mix(in srgb, var(--paper-2) 85%, white)',
            }}
          />
        </div>
        <div>
          <h3 className="section-title mb-2 text-sm">度 × 介数散点（J2）</h3>
          <div
            ref={scatterRef}
            className="w-full rounded-xl border"
            style={{
              height: Math.max(220, Math.min(10, rows.length) * 28 + 40),
              borderColor: 'var(--line)',
              background: 'color-mix(in srgb, var(--paper-2) 90%, white)',
            }}
          />
        </div>
      </div>

      <p className="text-sm leading-relaxed text-muted">
        Brandes 介数 + 度中心性 · {data.node_count ?? data.metrics.length} 节点
        {data.generated && ` · ${data.generated}`}。
        <strong style={{ color: 'var(--ink)' }}> J3</strong>：关系图谱可切换「SNA 节点大小」叠加介数。
        URL <code>?focus=人物</code> 高亮表格；点击条形图跳转图谱。
      </p>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[800px] border-collapse text-sm">
          <thead>
            <tr className="text-muted" style={{ borderBottom: '1.5px solid var(--line)' }}>
              <th className="px-3 py-2 text-left font-normal">介#</th>
              <th className="px-3 py-2 text-left font-normal">度#</th>
              <th className="px-3 py-2 text-left font-normal">人物</th>
              <th className="px-3 py-2 text-left font-normal">派系</th>
              <th className="px-3 py-2 text-left font-normal">距离</th>
              <th className="px-3 py-2 text-right font-normal">度</th>
              <th className="px-3 py-2 text-right font-normal">介数</th>
              <th className="px-3 py-2 text-left font-normal">派系内</th>
              <th className="px-3 py-2 text-left font-normal">联动</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => {
              const txs = silverLinks[m.id] ?? [];
              const chainEvts = chainEventsForCharacter(bookSlug, m.id);
              const isFocus = focusId === m.id;
              return (
                <tr
                  key={m.id}
                  data-sna-focus={isFocus ? 'true' : undefined}
                  className="cursor-pointer hover:opacity-90"
                  style={{
                    borderBottom: '1px solid var(--line)',
                    background: isFocus ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : undefined,
                  }}
                  onClick={() => applyFocus(m.id)}
                >
                  <td className="px-3 py-2.5 text-muted tabular-nums">{m.betweenness_rank ?? '—'}</td>
                  <td className="px-3 py-2.5 text-muted tabular-nums">{m.degree_rank ?? '—'}</td>
                  <td className="px-3 py-2.5 font-medium">
                    <a
                      href={characterHref(bookSlug, m.id)}
                      className="hover:underline"
                      style={{ color: 'var(--ink)' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {m.id}
                    </a>
                  </td>
                  <td className="px-3 py-2.5 text-muted">{m.faction ?? '—'}</td>
                  <td className="px-3 py-2.5 text-muted">{proximityLabel(m.ximen_proximity)}</td>
                  <td className="px-3 py-2.5 text-right tabular-nums">{m.degree}</td>
                  <td className="px-3 py-2.5 text-right tabular-nums">{m.betweenness.toFixed(4)}</td>
                  <td className="px-3 py-2.5">
                    <span className="chip text-xs">{rankLabel((m.faction_rank ?? 1) - 1)}</span>
                  </td>
                  <td className="px-3 py-2.5 text-xs" onClick={(e) => e.stopPropagation()}>
                    <a href={graphFocusHref(bookSlug, m.id)} className="mr-2 hover:underline" style={{ color: 'var(--accent)' }}>
                      图谱
                    </a>
                    {txs.length > 0 && (
                      <a href={silverHref(bookSlug, txs[0]!)} className="mr-2 hover:underline" style={{ color: 'var(--accent)' }}>
                        银 {txs.length}
                      </a>
                    )}
                    {chainEvts.length > 0 ? (
                      <a
                        href={chainEventHref(bookSlug, chainEvts[0]!.id)}
                        className="hover:underline"
                        style={{ color: 'var(--accent)' }}
                        title={chainEvts.map((e) => e.title).join(' · ')}
                      >
                        链 {chainEvts.length}
                      </a>
                    ) : (
                      <a href={`/${bookSlug}/chain`} className="hover:underline" style={{ color: 'var(--accent)' }}>
                        链
                      </a>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted">
        深度阅读：
        <a href={`/${bookSlug}/topics/帮闲圈分析`} className="ml-1 hover:underline" style={{ color: 'var(--accent)' }}>
          帮闲圈分析 topic
        </a>
        · <code>python scripts/build_sna.py 金瓶梅</code>
      </p>
    </div>
  );
}
