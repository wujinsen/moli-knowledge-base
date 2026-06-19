import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import { graphTheme } from '../lib/graphTheme';
import {
  ZONE_COLORS,
  ZONE_LABELS,
  zoneColor,
  type TownMapData,
  type TownMapNode,
  type TownZone,
} from '../lib/townMap';

interface Props {
  data: TownMapData;
  bookSlug: string;
  initialRouteId?: string | null;
}

type ZoneFilter = 'all' | TownZone;

export default function TownMap({ data, bookSlug, initialRouteId = null }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const [zone, setZone] = useState<ZoneFilter>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const zoneRef = useRef<ZoneFilter>(zone);
  zoneRef.current = zone;

  const routes = data.routes ?? [];
  const [activeRouteId, setActiveRouteId] = useState<string | null>(
    initialRouteId && routes.some((r) => r.id === initialRouteId) ? initialRouteId : null,
  );
  const activeRoute = activeRouteId ? routes.find((r) => r.id === activeRouteId) ?? null : null;

  const nodeById = useMemo(
    () => new Map(data.nodes.map((n) => [n.id, n])),
    [data.nodes],
  );

  const zones = useMemo(
    () => [...new Set(data.nodes.map((n) => n.zone))] as TownZone[],
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
  const visibleEdges = useMemo(
    () =>
      data.edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [data.edges, visibleIds],
  );

  const selectedNode = selectedId ? nodeById.get(selectedId) ?? null : null;

  const buildOption = useCallback((): EChartsOption => {
    const route = activeRouteId ? (data.routes ?? []).find((r) => r.id === activeRouteId) ?? null : null;
    const routeOrder = new Map<string, number>();
    if (route) route.stops.forEach((s, i) => routeOrder.set(s.id, i + 1));
    const routeActive = !!route;
    return {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 800,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: gt.accentLine,
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 13 },
        formatter: (p: unknown) => {
          const params = p as { dataType?: string; data?: Record<string, unknown> };
          if (params.dataType === 'edge') return '';
          const d = params.data ?? {};
          const node = nodeById.get((d.id as string) ?? '');
          if (!node) return '';
          const ch = node.chapters.length
            ? `<br/><span style="color:${gt.accent}">第${node.chapters.slice(0, 4).join('、')}${node.chapters.length > 4 ? '…' : ''}回</span>`
            : '';
          return `<strong style="font-size:15px">${node.name}</strong><br/>${ZONE_LABELS[node.zone]}${ch}`;
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'none',
          roam: true,
          draggable: false,
          data: visibleNodes.map((n) => {
            const color = zoneColor(n.zone);
            const selected = n.id === selectedId;
            const inManor = n.zone === '府内';
            const baseSize = n.id === '西门府' || n.id === '清河县' ? 28 : inManor ? 18 : 20;
            const order = routeOrder.get(n.id);
            const onRoute = order != null;
            const dimmed = routeActive && !onRoute;
            const isEnd = onRoute && order === route!.stops.length;
            const routeColor = isEnd ? '#f97316' : '#fcd34d';
            const size = onRoute ? baseSize * 1.25 : selected ? baseSize * 1.3 : baseSize;
            return {
              id: n.id,
              name: n.name,
              x: n.x,
              y: n.y,
              symbol: inManor && n.parent ? 'roundRect' : n.zone === '寺观' ? 'diamond' : 'circle',
              symbolSize: size,
              itemStyle: {
                color: onRoute ? routeColor : color,
                borderColor: onRoute ? '#fff7ed' : selected ? '#fff' : 'rgba(255,255,255,0.35)',
                borderWidth: onRoute ? 2.5 : selected ? 2.5 : 1.2,
                shadowBlur: onRoute ? 26 : selected ? 28 : 12,
                shadowColor: onRoute ? routeColor : color,
                opacity: dimmed ? 0.16 : 1,
              },
              label: {
                show: !dimmed,
                position: 'bottom',
                distance: 6,
                color: onRoute ? routeColor : selected ? '#fff' : '#e8eef7',
                fontSize: onRoute ? 13 : selected ? 13 : 11,
                fontWeight: onRoute || selected ? 600 : 400,
                formatter: onRoute ? `${order}. ${n.name}` : undefined,
              },
            };
          }),
          edges: [
            ...visibleEdges.map((e) => ({
              source: e.source,
              target: e.target,
              lineStyle: {
                color: e.kind === 'parent' ? 'rgba(212,160,23,0.45)' : gt.accent,
                width: e.kind === 'parent' ? 1 : 1.5,
                type: (e.kind === 'parent' ? 'dashed' : 'solid') as 'dashed' | 'solid',
                opacity: routeActive ? 0.06 : 0.65,
                curveness: 0.08,
              },
            })),
            ...(route
              ? route.stops.slice(0, -1).map((s, i) => ({
                  source: s.id,
                  target: route.stops[i + 1].id,
                  symbol: ['none', 'arrow'] as [string, string],
                  symbolSize: 11,
                  lineStyle: {
                    color: '#fcd34d',
                    width: 3,
                    type: 'solid' as const,
                    opacity: 0.95,
                    curveness: 0.06,
                    shadowBlur: 8,
                    shadowColor: 'rgba(252,211,77,0.5)',
                  },
                }))
              : []),
          ],
        },
      ],
    };
  }, [visibleNodes, visibleEdges, selectedId, nodeById, gt, activeRouteId, data.routes]);

  useEffect(() => {
    const el = chartRef.current;
    const container = containerRef.current;
    if (!el) return;

    let chart: echarts.ECharts | null = null;
    let rafId = 0;
    let attempts = 0;
    let cancelled = false;

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
          if (!id) return;
          setActiveRouteId(null);
          // 点西门府：钻入府内七进子布局（ECharts 自动缩放铺满）
          if (id === '西门府' && zoneRef.current !== '府内') {
            setZone('府内');
            setSelectedId('西门府');
            return;
          }
          setSelectedId((prev) => (prev === id ? null : id));
        }
      });
      chart.getZr().on('click', (e) => {
        if (!e.target) setSelectedId(null);
      });
      chart.setOption(buildOption(), { notMerge: true });
      window.setTimeout(() => chart?.resize(), 0);
    };

    const onResize = () => {
      if (!chart) {
        attempts = 0;
        mountChart();
      } else chart.resize();
    };

    const ro = new ResizeObserver(onResize);
    ro.observe(el);
    if (container && container !== el) ro.observe(container);

    mountChart();
    window.addEventListener('resize', onResize);
    window.addEventListener('graph-chrome-sync', onResize);

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      ro.disconnect();
      window.removeEventListener('resize', onResize);
      window.removeEventListener('graph-chrome-sync', onResize);
      chart?.dispose();
      chartInstance.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount once; option updates in separate effect
  }, []);

  useEffect(() => {
    chartInstance.current?.setOption(buildOption(), { notMerge: true });
  }, [buildOption]);

  const resetView = () => {
    setSelectedId(null);
    setZone('all');
    setActiveRouteId(null);
    chartInstance.current?.dispatchAction({ type: 'restore' });
  };

  const selectRoute = (id: string) => {
    setActiveRouteId((prev) => (prev === id ? null : id));
    setSelectedId(null);
    setZone('all');
  };

  const zoneButtons: { key: ZoneFilter; label: string }[] = [
    { key: 'all', label: '全部' },
    ...zones.map((z) => ({ key: z as ZoneFilter, label: ZONE_LABELS[z] })),
  ];

  return (
    <div ref={containerRef} className="graph-explorer town-explorer relative w-full overflow-hidden">
      <div className="pointer-events-none absolute inset-0" aria-hidden style={{ background: gt.backdrop }} />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        aria-hidden
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <div className="absolute left-0 right-0 top-12 z-10 flex flex-wrap items-center gap-2 p-3">
        <div className="flex flex-wrap gap-1 rounded-lg border border-white/10 bg-slate-900/80 p-1 backdrop-blur-sm">
          {zoneButtons.map((b) => (
            <button
              key={b.key}
              type="button"
              onClick={() => {
                setActiveRouteId(null);
                setZone(b.key);
              }}
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
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-300 backdrop-blur-sm hover:border-white/20 hover:text-white"
        >
          重置视图
        </button>
        <div className="ml-auto flex gap-3 text-xs text-slate-400">
          <span>{visibleNodes.length} 处</span>
          <span>{visibleEdges.length} 条邻接</span>
        </div>
      </div>

      {zone === '府内' && (
        <button
          type="button"
          onClick={resetView}
          className="absolute left-1/2 top-24 z-20 -translate-x-1/2 rounded-full border px-3.5 py-1.5 text-xs font-medium backdrop-blur-md transition-colors"
          style={{
            borderColor: gt.accentLine,
            backgroundColor: 'rgba(15,23,42,0.9)',
            color: gt.accentSoft,
          }}
        >
          西门府七进 · 点此 ← 返回清河全图
        </button>
      )}

      {routes.length > 0 && (
        <div className="absolute left-3 top-24 z-20 flex max-h-[calc(100%-12rem)] w-56 flex-col overflow-hidden rounded-lg border border-white/10 bg-slate-900/90">
          <div className="flex items-center justify-between px-2.5 pt-2 text-xs font-medium text-amber-200/90">
            <span>事件路线</span>
            {activeRouteId && (
              <button
                type="button"
                onClick={() => setActiveRouteId(null)}
                className="rounded px-1.5 text-[11px] text-slate-400 hover:text-white"
              >
                清除
              </button>
            )}
          </div>
          <div className="mt-1 flex flex-col gap-0.5 overflow-y-auto px-1.5 pb-2">
            {routes.map((r) => {
              const on = r.id === activeRouteId;
              return (
                <div
                  key={r.id}
                  className="rounded-md"
                  style={{ backgroundColor: on ? 'rgba(212,160,23,0.14)' : 'transparent' }}
                >
                  <button
                    type="button"
                    onClick={() => selectRoute(r.id)}
                    className="block w-full rounded-md px-2 py-1.5 text-left text-xs leading-snug transition-colors"
                    style={{ color: on ? '#fcd34d' : '#cbd5e1' }}
                  >
                    <span className="block">{r.title}</span>
                    {r.chapters.length > 0 && (
                      <span className="text-[10px] text-slate-500">
                        第{r.chapters.join('、')}回 · {r.stops.length}站
                      </span>
                    )}
                  </button>
                  {on && (
                    <div className="px-2 pb-2 pt-0.5">
                      {r.summary && (
                        <p className="mb-1.5 text-[11px] leading-relaxed text-slate-300">{r.summary}</p>
                      )}
                      <div className="mb-1.5 flex flex-wrap items-center gap-x-1 text-[11px]">
                        {r.stops.map((s, i) => (
                          <span key={s.id} className="inline-flex items-center">
                            {i > 0 && <span className="mx-0.5 text-slate-600">→</span>}
                            <a
                              href={`/${bookSlug}/l/${encodeURIComponent(s.id)}`}
                              className="text-slate-400 underline-offset-2 hover:text-amber-200 hover:underline"
                            >
                              {s.name}
                            </a>
                          </span>
                        ))}
                      </div>
                      <a
                        href={`/${bookSlug}/e/${encodeURIComponent(r.id)}`}
                        className="inline-block rounded bg-amber-500/15 px-2 py-0.5 text-[11px] text-amber-200 transition-colors hover:bg-amber-500/25"
                      >
                        事件详情 →
                      </a>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeRoute && (
        <div className="pointer-events-none absolute left-1/2 top-24 z-20 max-w-md -translate-x-1/2 rounded-md bg-slate-900/92 px-3 py-1.5 text-center text-xs text-amber-100/90">
          {activeRoute.stops.map((s) => s.name).join(' → ')}
        </div>
      )}

      <div className="absolute bottom-4 left-3 z-10 flex flex-wrap gap-x-3 gap-y-1.5 rounded-lg border border-white/10 bg-slate-900/85 p-2.5 backdrop-blur-md">
        {zones.map((z) => (
          <span key={z} className="flex items-center gap-1.5 text-xs text-slate-300">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ZONE_COLORS[z] }} />
            {ZONE_LABELS[z]}
          </span>
        ))}
        <span className="text-xs text-slate-500">虚线 = 隶属 · 实线 = 邻近</span>
      </div>

      {selectedNode && (
        <aside
          className="absolute right-3 top-28 z-10 max-h-[calc(100vh-6rem)] w-64 overflow-y-auto rounded-xl border bg-slate-900/90 p-4 shadow-xl backdrop-blur-md"
          style={{ borderColor: gt.accentLine }}
        >
          <div className="mb-1 text-lg font-semibold" style={{ color: gt.accentSoft }}>
            {selectedNode.name}
          </div>
          <div className="mb-2 text-xs text-slate-400">
            {ZONE_LABELS[selectedNode.zone]}
            {selectedNode.category ? ` · ${selectedNode.category}` : ''}
          </div>
          <p className="mb-3 text-sm leading-snug text-slate-300">{selectedNode.summary}</p>

          {selectedNode.events.length > 0 && (
            <div className="mb-3">
              <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">链上事件</div>
              <div className="flex flex-wrap gap-1">
                {selectedNode.events.map((ev) => (
                  <a
                    key={ev.id}
                    href={`/${bookSlug}/e/${ev.id}`}
                    className="rounded px-1.5 py-0.5 text-xs hover:underline"
                    style={{ backgroundColor: `${gt.accent}1a`, color: gt.accentSoft }}
                  >
                    {ev.title}
                  </a>
                ))}
              </div>
            </div>
          )}

          {selectedNode.items.length > 0 && (
            <div className="mb-3">
              <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">相关名物</div>
              <div className="flex flex-wrap gap-1">
                {selectedNode.items.map((item) => (
                  <span
                    key={item}
                    className="rounded border border-white/10 px-1.5 py-0.5 text-xs text-slate-300"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {selectedNode.chapters.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-1">
              {selectedNode.chapters.slice(0, 8).map((c) => (
                <a
                  key={c}
                  href={`/${bookSlug}/read/${c}`}
                  className="rounded border border-white/10 px-1.5 py-0.5 text-xs text-slate-300 hover:border-white/30 hover:text-white"
                >
                  第{c}回
                </a>
              ))}
            </div>
          )}

          <div className="flex flex-col gap-2">
            {selectedNode.id === '西门府' && zone !== '府内' && (
              <button
                type="button"
                onClick={() => setZone('府内')}
                className="rounded-md border px-2.5 py-1.5 text-sm font-medium transition-colors"
                style={{ borderColor: gt.accentLine, color: gt.accentSoft, backgroundColor: `${gt.accent}1a` }}
              >
                展开府内七进 →
              </button>
            )}
            <a
              href={`/${bookSlug}/l/${encodeURIComponent(selectedNode.id)}`}
              className="text-sm hover:underline"
              style={{ color: gt.accent }}
            >
              地点详情 →
            </a>
            <a href={`/${bookSlug}/places`} className="text-xs text-slate-500 hover:text-slate-300">
              建筑居所目录
            </a>
          </div>
        </aside>
      )}

      <div ref={chartRef} className="absolute inset-0 h-full w-full" />

      <p className="pointer-events-none absolute bottom-4 left-1/2 z-0 -translate-x-1/2 select-none text-center text-xs text-slate-600/70">
        节点按原文方位摆放（上北下南·左西右东）· 点西门府展开府内七进 · 滚轮缩放
      </p>
    </div>
  );
}
