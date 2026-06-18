import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import {
  characterHref,
  filterMetrics,
  graphFocusHref,
  proximityLabel,
  rankLabel,
  silverHref,
  type SnaData,
} from '../lib/sna';
import { chainEventsForCharacter } from '../lib/chainIndex';
import { chainEventHref } from '../lib/chain';

interface Props {
  data: SnaData;
  bookSlug: string;
}

const BANGXIAN = '帮闲圈';

export default function SnaDashboard({ data, bookSlug }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);
  const [faction, setFaction] = useState<string | undefined>(undefined);
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

  const rows = useMemo(() => filterMetrics(data, faction).slice(0, 14), [data, faction]);
  const factionKeys = useMemo(
    () => Object.keys(data.factions ?? {}).sort((a, b) => a.localeCompare(b, 'zh')),
    [data.factions],
  );

  const chartOption = useMemo((): EChartsOption => {
    const top = rows.slice(0, 10);
    return {
      backgroundColor: 'transparent',
      grid: { left: 72, right: 24, top: 8, bottom: 24 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 14 },
      },
      xAxis: {
        type: 'value',
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
          data: top.map((m) => m.betweenness).reverse(),
          itemStyle: { color: '#607a67', borderRadius: [0, 4, 4, 0] },
          barMaxWidth: 18,
        },
      ],
    };
  }, [rows]);

  const render = useCallback(() => {
    if (!chartRef.current) return;
    if (!inst.current) inst.current = echarts.init(chartRef.current);
    inst.current.setOption(chartOption, true);
  }, [chartOption]);

  useEffect(() => {
    render();
    const ro = new ResizeObserver(() => inst.current?.resize());
    if (chartRef.current) ro.observe(chartRef.current);
    return () => {
      ro.disconnect();
      inst.current?.dispose();
      inst.current = null;
    };
  }, [render]);

  const bangxian = data.bangxian_hubs ?? [];
  const silverLinks = data.silver_links ?? {};

  return (
    <div className="sna-dashboard space-y-8">
      <div className="grid gap-3 sm:grid-cols-3">
        {data.hubs.slice(0, 3).map((id, i) => (
          <a
            key={id}
            href={graphFocusHref(bookSlug, id)}
            className="rounded-xl border px-4 py-3 transition hover:opacity-90"
            style={{ borderColor: 'var(--line)', background: 'var(--surface)' }}
          >
            <div className="text-xs text-muted">
              全书介数 Top {i + 1}
            </div>
            <div className="brand mt-1 text-xl" style={{ color: 'var(--primary)' }}>
              {id}
            </div>
          </a>
        ))}
      </div>

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
          全部
        </button>
        {factionKeys.map((f) => (
          <button
            key={f}
            type="button"
            className={`chip ${faction === f ? 'ring-1' : ''}`}
            style={{ borderColor: faction === f ? 'var(--accent)' : undefined }}
            onClick={() => setFaction(f)}
          >
            {f}
            {data.factions?.[f] && ` (${data.factions[f].count})`}
          </button>
        ))}
      </div>

      <div
        ref={chartRef}
        className="w-full rounded-xl border"
        style={{
          height: Math.max(220, rows.slice(0, 10).length * 28 + 40),
          borderColor: 'var(--line)',
          background: 'color-mix(in srgb, var(--paper-2) 85%, white)',
        }}
      />

      <p className="text-sm leading-relaxed text-muted">
        无向图近似 · Brandes 介数中心性 · {data.node_count ?? data.metrics.length} 节点
        {data.generated && ` · ${data.generated}`}。        点击人物跳转
        <strong style={{ color: 'var(--ink)' }}> 关系图谱高亮</strong>；有白银记录者链至
        <a href={`/${bookSlug}/silver`} className="mx-1 hover:underline" style={{ color: 'var(--accent)' }}>
          白银流
        </a>
        ，与
        <a href={`/${bookSlug}/chain`} className="mx-1 hover:underline" style={{ color: 'var(--accent)' }}>
          衰败链
        </a>
        互证。URL 加 <code>?focus=人物</code> 可高亮表格行。
      </p>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr class="text-muted" style="border-bottom: 1.5px solid var(--line)">
              <th className="px-3 py-2 text-left font-normal">#</th>
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
            {rows.map((m, i) => {
              const txs = silverLinks[m.id] ?? [];
              const chainEvts = chainEventsForCharacter(bookSlug, m.id);
              const isFocus = focusId === m.id;
              return (
                <tr
                  key={m.id}
                  data-sna-focus={isFocus ? 'true' : undefined}
                  style={{
                    borderBottom: '1px solid var(--line)',
                    background: isFocus ? 'color-mix(in srgb, var(--accent) 8%, transparent)' : undefined,
                  }}
                >
                  <td className="px-3 py-2.5 text-muted">
                    {i + 1}
                  </td>
                  <td className="px-3 py-2.5 font-medium">
                    <a href={characterHref(bookSlug, m.id)} className="hover:underline" style={{ color: 'var(--ink)' }}>
                      {m.id}
                    </a>
                  </td>
                  <td className="px-3 py-2.5 text-muted">
                    {m.faction ?? '—'}
                  </td>
                  <td className="px-3 py-2.5 text-muted">
                    {proximityLabel(m.ximen_proximity)}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums">{m.degree}</td>
                  <td className="px-3 py-2.5 text-right tabular-nums">{m.betweenness.toFixed(4)}</td>
                  <td className="px-3 py-2.5">
                    <span className="chip text-xs">{rankLabel((m.faction_rank ?? 1) - 1)}</span>
                  </td>
                  <td className="px-3 py-2.5 text-xs">
                    <a href={graphFocusHref(bookSlug, m.id)} className="mr-2 hover:underline" style={{ color: 'var(--accent)' }}>
                      图谱
                    </a>
                    {txs.length > 0 && (
                      <a href={silverHref(bookSlug, txs[0]!)} className="mr-2 hover:underline" style={{ color: 'var(--accent)' }}>
                        银 {txs.length} 笔
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
        · 运行 <code>python scripts/build_sna.py 金瓶梅</code> 重建指标
      </p>
    </div>
  );
}
