import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import {
  filterSilver,
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

export interface SilverTrackFilter {
  id: string;
  label: string;
  color: string;
  txIds: string[];
}

interface Props {
  data: SilverData;
  bookSlug: string;
  txRows: TxRow[];
  initialChapter?: number;
  highlightTx?: string;
  /** event id → transaction_refs（chain P4 互链） */
  eventTxMap?: Record<string, string[]>;
  /** build_financial.json 专题轨（J3 筛选） */
  tracks?: SilverTrackFilter[];
}

function scrollToTx(id: string) {
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  el.classList.add('silver-row-active');
  window.setTimeout(() => el.classList.remove('silver-row-active'), 2400);
}

function readUrlState() {
  const params = new URLSearchParams(window.location.search);
  const ch = params.get('chapter');
  const track = params.get('track');
  return {
    chapter: ch ? Number(ch) : null,
    track,
  };
}

function syncUrl(chapter: number, trackId: string | null) {
  const url = new URL(window.location.href);
  url.searchParams.set('chapter', String(chapter));
  if (trackId) url.searchParams.set('track', trackId);
  else url.searchParams.delete('track');
  window.history.replaceState({}, '', url.toString());
}

export default function SilverDashboard({
  data,
  bookSlug,
  txRows,
  initialChapter,
  highlightTx,
  eventTxMap = {},
  tracks = [],
}: Props) {
  const sankeyRef = useRef<HTMLDivElement>(null);
  const poolRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const sankeyInst = useRef<echarts.ECharts | null>(null);
  const poolInst = useRef<echarts.ECharts | null>(null);
  const timelineInst = useRef<echarts.ECharts | null>(null);

  const [maxChapter, setMaxChapter] = useState(initialChapter ?? data.chapter_max);
  const [activeTrack, setActiveTrack] = useState<string | null>(null);
  const [activeTxs, setActiveTxs] = useState<string[]>(highlightTx ? [highlightTx] : []);
  const [linkedEvent, setLinkedEvent] = useState<string | null>(null);

  const trackTxSet = useMemo(() => {
    if (!activeTrack) return null;
    const t = tracks.find((x) => x.id === activeTrack);
    return t ? new Set(t.txIds) : null;
  }, [activeTrack, tracks]);

  const filtered = useMemo(
    () => filterSilver(data, { maxChapter, trackTxIds: trackTxSet }),
    [data, maxChapter, trackTxSet],
  );
  const sankey = useMemo(() => toSankey(filtered), [filtered]);

  useEffect(() => {
    const { chapter, track } = readUrlState();
    if (chapter && chapter >= data.chapter_min && chapter <= data.chapter_max) {
      setMaxChapter(chapter);
    }
    if (track && tracks.some((t) => t.id === track)) {
      setActiveTrack(track);
    }
  }, [data.chapter_min, data.chapter_max, tracks]);

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

  useEffect(() => {
    syncUrl(maxChapter, activeTrack);
  }, [maxChapter, activeTrack]);

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
            fontSize: 13,
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

  const poolOption = useMemo((): EChartsOption => {
    const sorted = [...filtered.pools]
      .filter((p) => p.name !== filtered.hub.name)
      .sort((a, b) => Math.max(b.inflow, b.outflow) - Math.max(a.inflow, a.outflow))
      .slice(0, 10);
    return {
      backgroundColor: 'transparent',
      grid: { left: 88, right: 16, top: 8, bottom: 24 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
      },
      legend: {
        data: ['流入', '流出'],
        bottom: 0,
        textStyle: { color: '#5c6359', fontSize: 12 },
      },
      xAxis: {
        type: 'value',
        name: '两',
        nameTextStyle: { color: '#5c6359', fontSize: 12 },
        axisLabel: { color: '#5c6359', fontSize: 12 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.12)' } },
      },
      yAxis: {
        type: 'category',
        data: sorted.map((p) => p.name),
        axisLabel: { color: '#1f261f', fontSize: 12 },
        axisLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.35)' } },
      },
      series: [
        {
          name: '流入',
          type: 'bar',
          data: sorted.map((p) => ({ value: p.inflow, itemStyle: { color: p.color } })),
        },
        {
          name: '流出',
          type: 'bar',
          data: sorted.map((p) => ({ value: p.outflow, itemStyle: { color: '#74332c' } })),
        },
      ],
    };
  }, [filtered]);

  const timelineOption = useMemo((): EChartsOption => {
    const pts = filtered.timeline;
    return {
      backgroundColor: 'transparent',
      grid: { left: 48, right: 16, top: 24, bottom: 32 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 14 },
        formatter: (params: { dataIndex?: number }[]) => {
          const idx = params[0]?.dataIndex ?? 0;
          const p = pts[idx];
          if (!p) return '';
          return `第 ${p.chapter} 回<br/>本回 +${p.delta} 两<br/>累计 ${p.cumulative} 两<br/><span style="opacity:0.7">点击筛选截止此回</span>`;
        },
      },
      xAxis: {
        type: 'category',
        data: pts.map((p) => `${p.chapter}`),
        axisLabel: { color: '#5c6359', fontSize: 14 },
        axisLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.35)' } },
      },
      yAxis: {
        type: 'value',
        name: '累计两',
        nameTextStyle: { color: '#5c6359', fontSize: 14 },
        axisLabel: { color: '#5c6359', fontSize: 14 },
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

  const bindTimelineClick = useCallback(() => {
    timelineInst.current?.off('click');
    timelineInst.current?.on('click', (p: { dataIndex?: number }) => {
      const ch = filtered.timeline[p.dataIndex ?? 0]?.chapter;
      if (ch != null) {
        setMaxChapter(ch);
        setActiveTxs([]);
      }
    });
  }, [filtered.timeline]);

  const renderCharts = useCallback(() => {
    try {
      if (sankeyRef.current) {
        if (!sankeyInst.current) sankeyInst.current = echarts.init(sankeyRef.current);
        sankeyInst.current.setOption(sankeyOption, true);
        bindSankeyClick();
      }
      if (poolRef.current) {
        if (!poolInst.current) poolInst.current = echarts.init(poolRef.current);
        poolInst.current.setOption(poolOption, true);
      }
      if (timelineRef.current) {
        if (!timelineInst.current) timelineInst.current = echarts.init(timelineRef.current);
        timelineInst.current.setOption(timelineOption, true);
        bindTimelineClick();
      }
    } catch (err) {
      console.error('[SilverDashboard] chart render failed', err);
    }
  }, [sankeyOption, poolOption, timelineOption, bindSankeyClick, bindTimelineClick]);

  useEffect(() => {
    renderCharts();
    const ro = new ResizeObserver(() => {
      sankeyInst.current?.resize();
      poolInst.current?.resize();
      timelineInst.current?.resize();
    });
    if (sankeyRef.current) ro.observe(sankeyRef.current);
    if (poolRef.current) ro.observe(poolRef.current);
    if (timelineRef.current) ro.observe(timelineRef.current);
    return () => {
      ro.disconnect();
      sankeyInst.current?.dispose();
      poolInst.current?.dispose();
      timelineInst.current?.dispose();
      sankeyInst.current = null;
      poolInst.current = null;
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
        <label className="flex min-w-[200px] flex-1 flex-col gap-1 text-sm text-muted">
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
            {activeTrack && ' · 专题轨筛选中'}
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

      {tracks.length > 0 && (
        <div className="mb-4">
          <p className="mb-2 text-xs text-muted">专题轨筛选（来自 build_financial.json）</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={`chip text-xs transition ${!activeTrack ? 'ring-2 ring-[var(--accent)]' : ''}`}
              onClick={() => {
                setActiveTrack(null);
                setActiveTxs([]);
              }}
            >
              全部
            </button>
            {tracks.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`chip text-xs transition ${activeTrack === t.id ? 'ring-2' : ''}`}
                style={{
                  borderColor: t.color,
                  ...(activeTrack === t.id ? { boxShadow: `0 0 0 2px ${t.color}` } : {}),
                }}
                onClick={() => {
                  setActiveTrack(activeTrack === t.id ? null : t.id);
                  setActiveTxs([]);
                }}
                title={`${t.txIds.length} 笔关联交易`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mb-3 flex flex-wrap gap-2">
        {topPools.map((p) => (
          <span
            key={p.name}
            className="chip text-xs text-muted"
            style={{ borderColor: p.color }}
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

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <h3 className="section-title mb-2 text-sm">桑基流向（J3）</h3>
          <div
            ref={sankeyRef}
            className="w-full rounded-xl border"
            style={{
              height: 440,
              borderColor: 'var(--line)',
              background: 'color-mix(in srgb, var(--paper-2) 80%, white)',
            }}
          />
        </div>
        <div className="lg:col-span-2">
          <h3 className="section-title mb-2 text-sm">资金池入出（J3）</h3>
          <div
            ref={poolRef}
            className="w-full rounded-xl border"
            style={{
              height: 440,
              borderColor: 'var(--line)',
              background: 'color-mix(in srgb, var(--paper-2) 90%, white)',
            }}
          />
        </div>
      </div>

      <p className="mt-2 text-xs text-muted">
        桑基节点宽度 ∝ 流量；点击流向带可定位下方交易。与{' '}
        <a href={`/${bookSlug}/chain`} className="hover:underline" style={{ color: 'var(--accent)' }}>
          衰败链
        </a>{' '}
        白银节点互证（<code>?event=</code> · <code>#jpm-tx-*</code>）。
        桑基图仅展示与西门庆府的净流向（双向合并）；不经 hub 的侧向流见资金池条形图。
      </p>

      <h3 className="section-title mb-2 mt-8 text-base">累计白银（按回 · J4）</h3>
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
