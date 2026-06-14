import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import {
  filterSilverByChapter,
  toSankey,
  type SilverData,
  POOL_COLORS,
} from '../lib/silver';

export interface TxRow {
  id: string;
  chapter: number;
  subtype: string;
  amount: string;
  parties: string;
  summary: string;
  disputed: boolean;
  href: string;
}

interface Props {
  data: SilverData;
  bookSlug: string;
  txRows: TxRow[];
  initialChapter?: number;
  highlightTx?: string;
  /** event id → transaction_refs（chain P4 互链） */
  eventTxMap?: Record<string, string[]>;
}

function scrollToTx(id: string) {
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  el.classList.add('silver-row-active');
  window.setTimeout(() => el.classList.remove('silver-row-active'), 2400);
}

export default function SilverDashboard({ data, bookSlug, txRows, initialChapter, highlightTx, eventTxMap = {} }: Props) {
  const sankeyRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const sankeyInst = useRef<echarts.ECharts | null>(null);
  const timelineInst = useRef<echarts.ECharts | null>(null);

  const [maxChapter, setMaxChapter] = useState(initialChapter ?? data.chapter_max);
  const [activeTxs, setActiveTxs] = useState<string[]>(highlightTx ? [highlightTx] : []);
  const [linkedEvent, setLinkedEvent] = useState<string | null>(null);

  const filtered = useMemo(() => filterSilverByChapter(data, maxChapter), [data, maxChapter]);
  const sankey = useMemo(() => toSankey(filtered), [filtered]);

  useEffect(() => {
    const fromHash = () => {
      const id = window.location.hash.replace('#', '');
      if (id.startsWith('jpm-tx')) {
        setActiveTxs([id]);
        scrollToTx(id);
      }
    };
    const fromQuery = () => {
      const eventId = new URLSearchParams(window.location.search).get('event');
      if (eventId && eventTxMap[eventId]?.length) {
        const txs = eventTxMap[eventId];
        setLinkedEvent(eventId);
        setActiveTxs(txs);
        scrollToTx(txs[0]!);
      } else {
        setLinkedEvent(null);
      }
    };
    fromHash();
    fromQuery();
    const onHash = () => fromHash();
    const onEvent = (e: Event) => {
      const id = (e as CustomEvent<string>).detail;
      if (id) {
        setActiveTxs([id]);
        scrollToTx(id);
      }
    };
    window.addEventListener('hashchange', onHash);
    window.addEventListener('silver-highlight', onEvent);
    return () => {
      window.removeEventListener('hashchange', onHash);
      window.removeEventListener('silver-highlight', onEvent);
    };
  }, [eventTxMap]);

  useEffect(() => {
    if (highlightTx) {
      scrollToTx(highlightTx);
      setActiveTxs([highlightTx]);
    }
  }, [highlightTx]);

  const sankeyOption = useMemo((): EChartsOption => {
    const nodeColors = sankey.nodes.map((n) => POOL_COLORS[n.name] ?? '#607a67');
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
        formatter: (p: { dataType?: string; name?: string; data?: { source?: string; target?: string; value?: number; txs?: string[] } }) => {
          if (p.dataType === 'edge' && p.data) {
            const txs = p.data.txs;
            const txLine = txs?.length ? `<br/>${txs.length} 笔 · 点击定位清单` : '';
            return `${p.data.source} → ${p.data.target}<br/><b>${p.data.value} 两</b>${txLine}`;
          }
          const pool = filtered.pools.find((x) => x.name === p.name);
          if (pool) {
            return `<b>${p.name}</b><br/>流入 ${pool.inflow} 两 · 流出 ${pool.outflow} 两<br/>净 ${pool.net >= 0 ? '+' : ''}${pool.net} 两`;
          }
          return `<b>${p.name ?? ''}</b>`;
        },
      },
      series: [
        {
          type: 'sankey',
          layoutIterations: 48,
          nodeGap: 12,
          nodeWidth: 20,
          nodeAlign: 'justify',
          draggable: false,
          emphasis: { focus: 'adjacency' },
          lineStyle: { color: 'gradient', curveness: 0.48, opacity: 0.5 },
          label: {
            color: '#1f261f',
            fontFamily: '"Noto Serif SC", serif',
            fontSize: 11,
            formatter: (p: { name?: string }) => {
              const pool = filtered.pools.find((x) => x.name === p.name);
              if (!pool || pool.name === filtered.hub.name) return p.name ?? '';
              const v = Math.max(pool.inflow, pool.outflow);
              return `${p.name}\n${v.toFixed(0)}两`;
            },
          },
          data: sankey.nodes.map((n, i) => ({
            name: n.name,
            depth: n.depth,
            value: n.value,
            itemStyle: { color: nodeColors[i] },
          })),
          links: sankey.links.map((l) => ({
            source: l.source,
            target: l.target,
            value: l.value,
            txs: l.txs,
          })),
        },
      ],
    };
  }, [sankey, filtered]);

  const timelineOption = useMemo((): EChartsOption => {
    const pts = filtered.timeline;
    return {
      backgroundColor: 'transparent',
      grid: { left: 48, right: 16, top: 24, bottom: 32 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 12 },
        formatter: (params: { dataIndex?: number }[]) => {
          const idx = params[0]?.dataIndex ?? 0;
          const p = pts[idx];
          if (!p) return '';
          return `第 ${p.chapter} 回<br/>本回 +${p.delta} 两<br/>累计 ${p.cumulative} 两`;
        },
      },
      xAxis: {
        type: 'category',
        data: pts.map((p) => `${p.chapter}`),
        axisLabel: { color: '#5c6359', fontSize: 10 },
        axisLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.35)' } },
      },
      yAxis: {
        type: 'value',
        name: '累计两',
        nameTextStyle: { color: '#5c6359', fontSize: 10 },
        axisLabel: { color: '#5c6359', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.15)' } },
      },
      series: [
        {
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#607a67', width: 2 },
          itemStyle: { color: '#9c8450' },
          areaStyle: { color: 'rgba(96, 122, 103, 0.12)' },
          data: pts.map((p) => p.cumulative),
        },
      ],
    };
  }, [filtered.timeline]);

  const bindSankeyClick = useCallback(() => {
    sankeyInst.current?.off('click');
    sankeyInst.current?.on('click', (p: { dataType?: string; data?: { txs?: string[] } }) => {
      if (p.dataType === 'edge' && p.data?.txs?.length) {
        setActiveTxs(p.data.txs);
        scrollToTx(p.data.txs[0]!);
      }
    });
  }, []);

  const renderCharts = useCallback(() => {
    if (sankeyRef.current) {
      if (!sankeyInst.current) sankeyInst.current = echarts.init(sankeyRef.current);
      sankeyInst.current.setOption(sankeyOption, true);
      bindSankeyClick();
    }
    if (timelineRef.current) {
      if (!timelineInst.current) timelineInst.current = echarts.init(timelineRef.current);
      timelineInst.current.setOption(timelineOption, true);
    }
  }, [sankeyOption, timelineOption, bindSankeyClick]);

  useEffect(() => {
    renderCharts();
    const ro = new ResizeObserver(() => {
      sankeyInst.current?.resize();
      timelineInst.current?.resize();
    });
    if (sankeyRef.current) ro.observe(sankeyRef.current);
    if (timelineRef.current) ro.observe(timelineRef.current);
    return () => {
      ro.disconnect();
      sankeyInst.current?.dispose();
      timelineInst.current?.dispose();
      sankeyInst.current = null;
      timelineInst.current = null;
    };
  }, [renderCharts]);

  const hub = filtered.hub;
  const topPools = [...filtered.pools]
    .filter((p) => p.name !== hub.name)
    .sort((a, b) => Math.max(b.inflow, b.outflow) - Math.max(a.inflow, a.outflow))
    .slice(0, 6);

  return (
    <div className="silver-dashboard">
      <div className="mb-4 flex flex-wrap items-end gap-4">
        <label className="flex min-w-[200px] flex-1 flex-col gap-1 text-sm" style={{ color: 'var(--ink-soft)' }}>
          <span>
            截止第 <strong style={{ color: 'var(--accent)' }}>{maxChapter}</strong> 回 · 已录入{' '}
            <strong style={{ color: 'var(--primary)' }}>{filtered.total_liang}</strong> 两（累计口径）
          </span>
          <input
            type="range"
            min={data.chapter_min}
            max={data.chapter_max}
            value={maxChapter}
            onChange={(e) => {
              setMaxChapter(Number(e.target.value));
              setActiveTxs([]);
            }}
            className="w-full accent-[#607a67]"
          />
          <span className="text-xs">
            第 {data.chapter_min}–{data.chapter_max} 回 · {filtered.transaction_count} 笔
            {filtered.disputed_count > 0 && ` · ${filtered.disputed_count} 笔存疑`}
          </span>
        </label>
        <div className="surface px-4 py-2 text-sm" style={{ borderColor: 'var(--line)' }}>
          <span className="chip text-xs">{hub.name}</span>
          <span className="ml-2" style={{ color: 'var(--ink)' }}>
            入 {hub.inflow} · 出 {hub.outflow} · 净 {hub.net >= 0 ? '+' : ''}
            {hub.net} 两
          </span>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {topPools.map((p) => (
          <span
            key={p.name}
            className="chip text-xs"
            style={{ borderColor: p.color, color: 'var(--ink-soft)' }}
            title={`流入 ${p.inflow} · 流出 ${p.outflow}`}
          >
            <span
              className="mr-1 inline-block h-2 w-2 rounded-full"
              style={{ background: p.color }}
            />
            {p.name}
          </span>
        ))}
      </div>

      <div
        ref={sankeyRef}
        className="w-full rounded-xl border"
        style={{
          height: 440,
          borderColor: 'var(--line)',
          background: 'color-mix(in srgb, var(--paper-2) 80%, white)',
        }}
      />

      <p className="mt-2 text-xs" style={{ color: 'var(--ink-soft)' }}>
        节点宽度 ∝ 流量；点击流向带可定位下方交易。与{' '}
        <a href={`/${bookSlug}/chain`} className="hover:underline" style={{ color: 'var(--accent)' }}>
          衰败链
        </a>{' '}
        白银节点互证。
      </p>

      <h3 className="section-title mb-2 mt-8 text-base">累计白银（按回）</h3>
      <div
        ref={timelineRef}
        className="w-full rounded-xl border"
        style={{
          height: 200,
          borderColor: 'var(--line)',
          background: 'color-mix(in srgb, var(--paper-2) 90%, white)',
        }}
      />

      {activeTxs.length > 0 && (
        <p className="mt-3 text-xs" style={{ color: 'var(--accent)' }}>
          高亮 {activeTxs.length} 笔关联交易：{activeTxs.join(' · ')}
          {linkedEvent && (
            <>
              {' · '}
              <a
                href={`/${bookSlug}/chain?focus=${encodeURIComponent(linkedEvent)}`}
                className="hover:underline"
              >
                衰败链节点
              </a>
            </>
          )}
        </p>
      )}

      <style>{`
        tr.silver-row-active td {
          background: color-mix(in srgb, var(--accent) 12%, transparent);
        }
        tr[data-silver-highlight="true"] td {
          background: color-mix(in srgb, var(--primary) 8%, transparent);
        }
      `}</style>

      {/* sync table row highlight via data attribute */}
      <TableHighlight activeTxs={activeTxs} txRows={txRows} />
    </div>
  );
}

function TableHighlight({ activeTxs, txRows }: { activeTxs: string[]; txRows: TxRow[] }) {
  useEffect(() => {
    for (const r of txRows) {
      const el = document.getElementById(r.id);
      if (!el) continue;
      if (activeTxs.includes(r.id)) {
        el.setAttribute('data-silver-highlight', 'true');
      } else {
        el.removeAttribute('data-silver-highlight');
      }
    }
  }, [activeTxs, txRows]);
  return null;
}
