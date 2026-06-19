import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import { graphTheme } from '../lib/graphTheme';
import {
  CAPITAL_CHAPTER_PRESETS,
  CAPITAL_GUIDES,
  CAPITAL_ZONE_COLORS,
  CAPITAL_ZONE_LABELS,
  CAPITAL_ZONE_ORDER,
  buildCapitalEdges,
  capitalZoneColor,
  type CapitalMapData,
  type CapitalMapNode,
  type CapitalZone,
} from '../lib/capitalMap';
import CapitalZoneCatalog from './CapitalZoneCatalog';
import MapCrossLinks from './MapCrossLinks';

interface Props {
  data: CapitalMapData;
  bookSlug: string;
}

type ZoneFilter = 'all' | CapitalZone;

function nodeSize(zone: CapitalZone): number {
  if (zone === '连接') return 18;
  if (zone === '都城') return 28;
  if (zone === '王府') return 24;
  return 20;
}

export default function CapitalMap({ data, bookSlug }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [chartReady, setChartReady] = useState(false);

  const [zone, setZone] = useState<ZoneFilter>('all');
  const [showCatalog, setShowCatalog] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [chapterFilter, setChapterFilter] = useState<number | null>(null);
  const [activeGuide, setActiveGuide] = useState<string | null>(null);

  const guidePath = useMemo(() => {
    if (!activeGuide) return null;
    return CAPITAL_GUIDES.find((g) => g.key === activeGuide)?.path ?? null;
  }, [activeGuide]);

  const nodeById = useMemo(
    () => new Map(data.nodes.map((n) => [n.id, n])),
    [data.nodes],
  );

  const zones = useMemo(
    () => CAPITAL_ZONE_ORDER.filter((z) => data.nodes.some((n) => n.zone === z)),
    [data.nodes],
  );

  const visibleNodes = useMemo(
    () => data.nodes.filter((n) => zone === 'all' || n.zone === zone),
    [data.nodes, zone],
  );
  const visibleIds = useMemo(
    () => new Set(visibleNodes.map((n) => n.id)),
    [visibleNodes],
  );

  const allEdges = useMemo(
    () => buildCapitalEdges(data.nodes, guidePath),
    [data.nodes, guidePath],
  );

  const visibleEdges = useMemo(
    () =>
      allEdges.filter((e) => {
        if (!visibleIds.has(e.source) || !visibleIds.has(e.target)) return false;
        if (e.kind === 'guide' && !activeGuide) return false;
        return true;
      }),
    [allEdges, visibleIds, activeGuide],
  );

  const selectedNode = selectedId ? nodeById.get(selectedId) ?? null : null;

  const buildOption = useCallback((): EChartsOption => {
    return {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 700,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: gt.accentLine,
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 14, fontFamily: '"Noto Serif SC", serif' },
        formatter: (p: unknown) => {
          const params = p as { dataType?: string; data?: Record<string, unknown> };
          if (params.dataType === 'edge') return '';
          const node = nodeById.get((params.data?.id as string) ?? '');
          if (!node) return '';
          const ch = node.chapters.length
            ? `<br/><span style="color:${gt.accent}">第${node.chapters.slice(0, 3).join('、')}${node.chapters.length > 3 ? '…' : ''}回</span>`
            : '';
          return `<strong style="font-size:16px">${node.name}</strong><br/>${CAPITAL_ZONE_LABELS[node.zone]}${ch}`;
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'none',
          roam: true,
          draggable: false,
          data: visibleNodes.map((n) => {
            const color = capitalZoneColor(n.zone);
            const selected = n.id === selectedId;
            const dimmed =
              chapterFilter != null && !n.chapters.includes(chapterFilter);
            const hasEvent =
              chapterFilter != null &&
              n.events.some((ev) => ev.chapters.includes(chapterFilter));
            const onGuide = guidePath?.includes(n.id) ?? false;
            const size = nodeSize(n.zone);
            return {
              id: n.id,
              name: n.name,
              x: n.x,
              y: n.y,
              symbol: n.zone === '连接' ? 'circle' : 'roundRect',
              symbolSize: selected ? size * 1.35 : onGuide && activeGuide ? size * 1.15 : size,
              itemStyle: {
                color,
                opacity: dimmed && !onGuide ? 0.28 : 1,
                borderColor: selected
                  ? '#fff'
                  : hasEvent || (onGuide && activeGuide)
                    ? '#fcd34d'
                    : 'rgba(255,255,255,0.35)',
                borderWidth: selected ? 2.5 : hasEvent || onGuide ? 2 : 1.2,
              },
              label: {
                show: true,
                position: 'bottom',
                distance: 6,
                color: selected ? '#fff' : dimmed && !onGuide ? 'rgba(241,245,249,0.45)' : '#e8eef7',
                fontSize: selected ? 14 : 12,
                fontWeight: selected ? 700 : 500,
              },
            };
          }),
          edges: visibleEdges.map((e) => ({
            source: e.source,
            target: e.target,
            symbol: e.kind !== 'nearby' ? ['none', 'arrow'] : ['none', 'none'],
            symbolSize: e.kind === 'nearby' ? 0 : [0, 9],
            lineStyle: {
              color: e.kind === 'guide' ? '#4ade80' : 'rgba(148,163,184,0.55)',
              width: e.kind === 'guide' ? 3 : 1.2,
              type: e.kind === 'nearby' ? 'solid' : 'dashed',
              opacity: e.kind === 'nearby' ? 0.45 : 0.88,
              curveness: e.kind === 'guide' ? 0.02 : 0.08,
            },
          })),
        },
      ],
    };
  }, [visibleNodes, visibleEdges, selectedId, nodeById, gt, chapterFilter, guidePath, activeGuide]);

  useEffect(() => {
    const el = chartRef.current;
    const container = containerRef.current;
    if (!el) return;

    let chart: echarts.ECharts | null = null;
    let cancelled = false;
    let attempts = 0;
    let rafId = 0;

    const mountChart = () => {
      if (cancelled || chart) return;
      if (el.clientWidth < 16 || el.clientHeight < 16) {
        attempts += 1;
        if (attempts > 240) return;
        cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(mountChart);
        return;
      }
      chart = echarts.init(el, undefined, { renderer: 'canvas' });
      chartInstance.current = chart;
      chart.on('click', (params) => {
        if (params.dataType === 'node' && params.data && typeof params.data === 'object') {
          const id = (params.data as { id?: string }).id;
          if (id) setSelectedId((prev) => (prev === id ? null : id));
        }
      });
      chart.getZr().on('click', (e) => {
        if (!e.target) setSelectedId(null);
      });
      chart.setOption(buildOption(), { notMerge: true });
      setChartReady(true);
      window.setTimeout(() => chart?.resize(), 0);
    };

    const onLayoutChange = () => {
      if (!chart) {
        attempts = 0;
        mountChart();
      } else chart.resize();
    };

    const ro = new ResizeObserver(onLayoutChange);
    ro.observe(el);
    if (container && container !== el) ro.observe(container);

    mountChart();

    window.addEventListener('resize', onLayoutChange);
    window.addEventListener('graph-chrome-sync', onLayoutChange);

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      ro.disconnect();
      window.removeEventListener('resize', onLayoutChange);
      window.removeEventListener('graph-chrome-sync', onLayoutChange);
      chart?.dispose();
      chartInstance.current = null;
      setChartReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount once
  }, []);

  useEffect(() => {
    if (!chartReady || !chartInstance.current) return;
    chartInstance.current.setOption(buildOption(), { notMerge: true });
    const t = window.setTimeout(() => chartInstance.current?.resize(), 0);
    return () => clearTimeout(t);
  }, [chartReady, buildOption]);

  const resetView = () => {
    setSelectedId(null);
    setZone('all');
    setChapterFilter(null);
    setActiveGuide(null);
    chartInstance.current?.dispatchAction({ type: 'restore' });
  };

  const activateGuide = (key: string) => {
    const g = CAPITAL_GUIDES.find((x) => x.key === key);
    if (!g) return;
    setActiveGuide((prev) => (prev === key ? null : key));
    setChapterFilter(g.chapter);
  };

  const zoneButtons: { key: ZoneFilter; label: string }[] = [
    { key: 'all', label: '全部' },
    ...zones.map((z) => ({ key: z as ZoneFilter, label: CAPITAL_ZONE_LABELS[z] })),
  ];

  const graphHeight = 'calc(100dvh - var(--graph-chrome, 10.5rem))';

  return (
    <div
      ref={containerRef}
      className="graph-explorer relative overflow-hidden"
      style={{ height: graphHeight, minHeight: graphHeight }}
    >
      <div className="pointer-events-none absolute inset-0" aria-hidden style={{ background: gt.backdrop }} />

      <div className="absolute left-0 right-0 top-0 z-10 flex flex-wrap items-center gap-2 p-3">
        <div className="flex flex-wrap gap-1 rounded-lg border border-white/10 bg-slate-900/80 p-1 backdrop-blur-sm">
          {zoneButtons.map((b) => (
            <button
              key={b.key}
              type="button"
              onClick={() => setZone(b.key)}
              className="rounded-md px-2.5 py-1 text-xs transition-colors"
              style={{
                backgroundColor: zone === b.key ? `${gt.accent}33` : 'transparent',
                color: zone === b.key ? gt.accentSoft : '#94a3b8',
              }}
            >
              {b.label}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-slate-900/80 px-2 py-1 backdrop-blur-sm">
          <span className="text-xs text-slate-400">回目</span>
          <select
            value={chapterFilter ?? ''}
            onChange={(e) => {
              const v = e.target.value;
              setChapterFilter(v === '' ? null : Number(v));
              setActiveGuide(null);
            }}
            className="max-w-[10rem] rounded-md border-0 bg-transparent py-1 text-xs text-slate-100 outline-none"
          >
            {CAPITAL_CHAPTER_PRESETS.map((p) => (
              <option key={p.label} value={p.chapter ?? ''} className="bg-slate-900">
                {p.label}
              </option>
            ))}
          </select>
        </label>
        {CAPITAL_GUIDES.map((g) => (
          <button
            key={g.key}
            type="button"
            onClick={() => activateGuide(g.key)}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-2.5 py-1.5 text-xs backdrop-blur-sm"
            style={{
              borderColor: activeGuide === g.key ? 'rgba(74,222,128,0.55)' : undefined,
              color: activeGuide === g.key ? '#86efac' : '#cbd5e1',
            }}
          >
            {g.label}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setShowCatalog((v) => !v)}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-xs text-slate-300 backdrop-blur-sm"
          style={{
            borderColor: showCatalog ? `${gt.accent}66` : undefined,
            color: showCatalog ? gt.accentSoft : undefined,
          }}
        >
          {showCatalog ? '隐藏名录' : '都外名录'}
        </button>
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-300 backdrop-blur-sm"
        >
          重置视图
        </button>
        <div className="ml-auto flex gap-3 text-xs text-slate-400">
          <span>{visibleNodes.length} 处</span>
          <span>{visibleEdges.length} 条边</span>
        </div>
      </div>

      <div className="absolute bottom-4 left-3 z-10 max-w-xl flex flex-wrap gap-x-3 gap-y-1.5 rounded-lg border border-white/10 bg-slate-900/85 p-2.5 backdrop-blur-md">
        {zones.map((z) => (
          <span key={z} className="flex items-center gap-1.5 text-xs text-slate-300">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: CAPITAL_ZONE_COLORS[z] }}
            />
            {CAPITAL_ZONE_LABELS[z]}
          </span>
        ))}
        <span className="text-xs text-slate-500">
          绿虚线 = 导览 · 实线 = 邻近
          {chapterFilter != null && ' · 淡色 = 该回未出场'}
        </span>
      </div>

      {showCatalog && (
        <CapitalZoneCatalog
          nodes={data.nodes}
          bookSlug={bookSlug}
          accent={gt.accent}
          accentSoft={gt.accentSoft}
          selectedId={selectedId}
          onSelect={(id) => setSelectedId((prev) => (prev === id ? null : id))}
        />
      )}

      {selectedNode && (
        <aside
          className="absolute right-3 top-16 z-10 max-h-[calc(100vh-6rem)] w-72 overflow-y-auto rounded-xl border bg-slate-900/90 p-4 shadow-xl backdrop-blur-md"
          style={{ borderColor: gt.accentLine }}
        >
          <div className="mb-1 text-lg font-semibold" style={{ color: gt.accentSoft }}>
            {selectedNode.name}
          </div>
          <div className="mb-2 text-xs text-slate-400">
            {CAPITAL_ZONE_LABELS[selectedNode.zone]}
            {selectedNode.category ? ` · ${selectedNode.category}` : ''}
          </div>
          {selectedNode.plaque && (
            <div className="mb-2 text-sm" style={{ color: gt.accentSoft }}>
              匾 · {selectedNode.plaque}
            </div>
          )}
          {selectedNode.couplet && (
            <div className="mb-2 text-xs leading-relaxed text-slate-400">
              {selectedNode.couplet.upper}；{selectedNode.couplet.lower}
            </div>
          )}
          <p className="mb-3 text-sm leading-snug text-slate-300">{selectedNode.summary}</p>

          {selectedNode.events.length > 0 && (
            <div className="mb-3">
              <div className="mb-1 text-xs font-semibold text-slate-500">关联大事</div>
              <div className="flex flex-col gap-1">
                {selectedNode.events.map((ev) => (
                  <a
                    key={ev.id}
                    href={`/${bookSlug}/e/${ev.id}`}
                    className="rounded border border-white/10 px-2 py-1 text-xs text-slate-300 hover:border-white/25"
                  >
                    {ev.title}
                    <span className="ml-1 text-slate-500">第{ev.chapters.join('、')}回</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {selectedNode.occupants.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-1">
              {selectedNode.occupants.map((o) => (
                <a
                  key={o}
                  href={`/${bookSlug}/c/${encodeURIComponent(o)}`}
                  className="rounded px-1.5 py-0.5 text-xs hover:underline"
                  style={{ backgroundColor: `${gt.accent}1a`, color: gt.accentSoft }}
                >
                  {o}
                </a>
              ))}
            </div>
          )}
          {selectedNode.chapters.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-1">
              {selectedNode.chapters.slice(0, 6).map((c) => (
                <a
                  key={c}
                  href={`/${bookSlug}/read/${c}`}
                  className="rounded border border-white/10 px-1.5 py-0.5 text-xs text-slate-300 hover:text-white"
                >
                  第{c}回
                </a>
              ))}
            </div>
          )}
          <div className="flex flex-col gap-2">
            <a
              href={`/${bookSlug}/l/${encodeURIComponent(selectedNode.id)}`}
              className="text-sm hover:underline"
              style={{ color: gt.accent }}
            >
              地点详情 →
            </a>
            <MapCrossLinks
              bookSlug={bookSlug}
              current="capital"
              nodeId={selectedNode.id}
            />
          </div>
        </aside>
      )}

      <div ref={chartRef} className="absolute inset-0 h-full w-full" />

      <p className="pointer-events-none absolute bottom-16 left-1/2 z-0 max-w-lg -translate-x-1/2 select-none text-center text-xs text-slate-600/80">
        坐标属 inference（都外拓扑），非测绘定稿 · 滚轮缩放 · 点击地点
      </p>
    </div>
  );
}
