import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import { graphTheme } from '../lib/graphTheme';
import {
  LAYER_LABELS,
  realmColor,
  type RouteData,
  type RouteLayer,
  type RouteNode,
} from '../lib/route';

interface Props {
  data: RouteData;
  bookSlug: string;
}

type LayerFilter = 'all' | RouteLayer;

type PathLabelOverlay = {
  key: string;
  x: number;
  y: number;
  bearing: string;
  distanceLi: number;
  active: boolean;
};

export default function RouteMap({ data, bookSlug }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const [layer, setLayer] = useState<LayerFilter>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const nodeById = useMemo(
    () => new Map(data.nodes.map((n) => [n.id, n])),
    [data.nodes],
  );

  const realms = useMemo(
    () => [...new Set(data.nodes.map((n) => n.realm))],
    [data.nodes],
  );

  const visibleNodes = useMemo(
    () => data.nodes.filter((n) => layer === 'all' || n.layer === layer),
    [data.nodes, layer],
  );
  const visibleIds = useMemo(
    () => new Set(visibleNodes.map((n) => n.id)),
    [visibleNodes],
  );
  const visibleEdges = useMemo(
    () => data.edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [data.edges, visibleIds],
  );

  const edgeByKey = useMemo(() => {
    const m = new Map<string, (typeof data.edges)[0]>();
    for (const e of data.edges) m.set(`${e.source}→${e.target}`, e);
    return m;
  }, [data.edges]);

  /** 凡间路线序 */
  const routePath = useMemo(
    () =>
      data.nodes
        .filter((n) => n.layer === 'real' && n.order != null)
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    [data.nodes],
  );

  /** 凡间路段序（用于交替弯折、路段表） */
  const routeLegs = useMemo(() => {
    const legs: {
      key: string;
      from: RouteNode;
      to: RouteNode;
      edge: (typeof data.edges)[0] | undefined;
    }[] = [];
    for (let i = 0; i < routePath.length - 1; i++) {
      const from = routePath[i];
      const to = routePath[i + 1];
      const key = `${from.id}→${to.id}`;
      legs.push({ key, from, to, edge: edgeByKey.get(key) });
    }
    return legs;
  }, [routePath, edgeByKey, data.edges]);

  const routeLegOrder = useMemo(
    () => new Map(routeLegs.map((l, i) => [l.key, i])),
    [routeLegs],
  );

  const [activeLegKey, setActiveLegKey] = useState<string | null>(null);
  const [hoverLegKey, setHoverLegKey] = useState<string | null>(null);
  const [pathLabels, setPathLabels] = useState<PathLabelOverlay[]>([]);

  /** 地图上只显示一条路段标签，避免密集区叠字 */
  const mapLabelLegKey = activeLegKey ?? hoverLegKey;

  /** 仅高亮当前选中的一条路段（避免多段同时亮 + 地图飘字） */
  const highlightedLegKeys = useMemo(() => {
    if (!activeLegKey) return new Set<string>();
    return new Set([activeLegKey]);
  }, [activeLegKey]);

  const selectedNode = selectedId ? nodeById.get(selectedId) ?? null : null;
  const activeLegEntry = useMemo(
    () => routeLegs.find((l) => l.key === activeLegKey) ?? null,
    [routeLegs, activeLegKey],
  );
  const activeLeg = activeLegEntry?.edge;

  /** 路径标签：仅当前选中/悬停路段，叠层跟漫游同步 */
  const syncPathLabels = useCallback(() => {
    const chart = chartInstance.current;
    const el = chartRef.current;
    if (!chart || !el || !mapLabelLegKey) {
      setPathLabels([]);
      return;
    }
    if (layer !== 'all' && layer !== 'real') {
      setPathLabels([]);
      return;
    }
    const leg = routeLegs.find((l) => l.key === mapLabelLegKey);
    if (!leg?.edge?.bearing || leg.edge.distanceLi == null) {
      setPathLabels([]);
      return;
    }
    const w = el.clientWidth;
    const h = el.clientHeight;
    const legIdx = routeLegOrder.get(leg.key) ?? 0;
    try {
      const p1 = chart.convertToPixel({ seriesIndex: 0 }, [leg.from.x, leg.from.y]) as
        | number[]
        | undefined;
      const p2 = chart.convertToPixel({ seriesIndex: 0 }, [leg.to.x, leg.to.y]) as
        | number[]
        | undefined;
      if (!p1 || !p2 || p1.length < 2 || p2.length < 2) {
        setPathLabels([]);
        return;
      }
      const mx = (p1[0] + p2[0]) / 2;
      const my = (p1[1] + p2[1]) / 2;
      const dx = p2[0] - p1[0];
      const dy = p2[1] - p1[1];
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy / len;
      const ny = dx / len;
      const side = legIdx % 2 === 0 ? 1 : -1;
      const x = mx + nx * 36 * side;
      const y = my + ny * 36 * side;
      if (!Number.isFinite(x) || !Number.isFinite(y) || x < -40 || y < -40 || x > w + 40 || y > h + 40) {
        setPathLabels([]);
        return;
      }
      setPathLabels([
        {
          key: leg.key,
          x,
          y,
          bearing: leg.edge.bearing,
          distanceLi: leg.edge.distanceLi,
          active: activeLegKey === leg.key,
        },
      ]);
    } catch {
      setPathLabels([]);
    }
  }, [routeLegs, routeLegOrder, layer, mapLabelLegKey, activeLegKey]);

  const buildOption = useCallback((): EChartsOption => {
    return {
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: gt.accentLine,
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 13 },
        formatter: (p: unknown) => {
          const params = p as {
            dataType?: string;
            data?: Record<string, unknown> & { source?: string; target?: string };
          };
          if (params.dataType === 'edge') {
            const src = params.data?.source as string | undefined;
            const tgt = params.data?.target as string | undefined;
            if (!src || !tgt) return '';
            const meta = edgeByKey.get(`${src}→${tgt}`);
            const from = nodeById.get(src)?.name ?? src;
            const to = nodeById.get(tgt)?.name ?? tgt;
            if (!meta?.bearing) return `<strong>${from}</strong> → ${to}`;
            return `<strong>${from}</strong> → ${to}<br/><span style="color:${gt.accent};font-size:17px;font-weight:700">${meta.bearing} · ${meta.distanceLi ?? '?'} 里</span>${meta.distanceKm != null ? `<span style="color:#94a3b8;font-size:14px">（约 ${meta.distanceKm} km）</span>` : ''}`;
          }
          const d = params.data ?? {};
          const node = nodeById.get((d.id as string) ?? '');
          if (!node) return '';
          const order = node.order != null ? `第 ${node.order} 站 · ` : '';
          const ch = node.chapters.length ? `<br/><span style="color:${gt.accent}">第${node.chapters.join('、')}回</span>` : '';
          return `<strong style="font-size:15px">${node.name}</strong><br/>${order}${node.realm}${ch}`;
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'none',
          roam: true,
          draggable: false,
          labelLayout: { hideOverlap: true },
          edgeLabel: { show: false },
          data: visibleNodes.map((n) => {
            const color = realmColor(n.realm);
            const isReal = n.layer === 'real';
            const selected = n.id === selectedId;
            const size = isReal ? (n.order != null ? 20 : 16) : 26;
            return {
              id: n.id,
              name: n.name,
              x: n.x,
              y: n.y,
              symbol: isReal ? 'circle' : 'diamond',
              symbolSize: selected ? size * 1.35 : size,
              itemStyle: {
                color,
                borderColor: selected ? '#fff' : 'rgba(255,255,255,0.35)',
                borderWidth: selected ? 2.5 : 1.2,
                shadowBlur: selected ? 30 : 14,
                shadowColor: color,
              },
              label: {
                show: true,
                position: isReal ? 'bottom' : 'top',
                distance: 7,
                color: selected ? '#fff' : '#e8eef7',
                fontSize: selected ? 13 : 11,
                fontWeight: selected || !isReal ? 600 : 400,
                formatter: () => n.name.replace(/^.*·/, ''),
              },
            };
          }),
          edges: visibleEdges.map((e) => {
            const key = `${e.source}→${e.target}`;
            const legIdx = routeLegOrder.get(key);
            const isHighlight = highlightedLegKeys.has(key);
            return {
              source: e.source,
              target: e.target,
              symbol: ['none', 'arrow'],
              symbolSize: [0, isHighlight ? 10 : 7],
              label: { show: false },
              lineStyle: {
                color: isHighlight ? gt.accentSoft : gt.accent,
                width: isHighlight ? 4 : 2.5,
                opacity: isHighlight ? 1 : 0.65,
                curveness: legIdx != null ? (legIdx % 2 === 0 ? 0.16 : -0.16) : 0.04,
              },
              emphasis: {
                lineStyle: { width: 4.5, opacity: 1, color: gt.accentSoft },
                label: { show: false },
              },
            };
          }),
        },
      ],
    };
  }, [visibleNodes, visibleEdges, selectedId, nodeById, edgeByKey, routeLegOrder, highlightedLegKeys, gt]);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current, undefined, { renderer: 'canvas' });
    chartInstance.current = chart;

    chart.on('click', (params) => {
      if (params.dataType === 'node' && params.data && typeof params.data === 'object') {
        const id = (params.data as { id?: string }).id;
        if (id) {
          setSelectedId((prev) => (prev === id ? null : id));
          const idx = routePath.findIndex((n) => n.id === id);
          if (idx > 0) setActiveLegKey(`${routePath[idx - 1].id}→${id}`);
          else setActiveLegKey(null);
        }
      }
      if (params.dataType === 'edge' && params.data && typeof params.data === 'object') {
        const src = (params.data as { source?: string }).source;
        const tgt = (params.data as { target?: string }).target;
        if (src && tgt) setActiveLegKey(`${src}→${tgt}`);
      }
    });
    chart.on('mouseover', (params) => {
      if (params.dataType === 'edge' && params.data && typeof params.data === 'object') {
        const src = (params.data as { source?: string }).source;
        const tgt = (params.data as { target?: string }).target;
        if (src && tgt && routeLegOrder.has(`${src}→${tgt}`)) {
          setHoverLegKey(`${src}→${tgt}`);
        }
      }
    });
    chart.on('mouseout', (params) => {
      if (params.dataType === 'edge') setHoverLegKey(null);
    });
    chart.getZr().on('click', (e) => {
      if (!e.target) {
        setSelectedId(null);
        setActiveLegKey(null);
        setHoverLegKey(null);
      }
    });

    const onResize = () => {
      chart.resize();
      syncPathLabels();
    };
    const onRoam = () => syncPathLabels();
    const onFinished = () => syncPathLabels();
    chart.on('graphRoam', onRoam);
    chart.on('finished', onFinished);
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.off('graphRoam', onRoam);
      chart.off('finished', onFinished);
      chart.dispose();
      chartInstance.current = null;
    };
  }, [syncPathLabels, routePath, routeLegOrder]);

  useEffect(() => {
    requestAnimationFrame(() => syncPathLabels());
  }, [mapLabelLegKey, syncPathLabels]);

  useEffect(() => {
    chartInstance.current?.setOption(buildOption(), { notMerge: true });
    requestAnimationFrame(() => syncPathLabels());
  }, [buildOption, syncPathLabels]);

  const resetView = () => {
    setSelectedId(null);
    setActiveLegKey(null);
    setHoverLegKey(null);
    setLayer('all');
    chartInstance.current?.dispatchAction({ type: 'restore' });
  };

  const toggleFullscreen = () => {
    const el = containerRef.current;
    if (!el) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else el.requestFullscreen();
  };

  const layerButtons: { key: LayerFilter; label: string }[] = [
    { key: 'all', label: '全部' },
    { key: 'real', label: LAYER_LABELS.real },
    { key: 'myth', label: LAYER_LABELS.myth },
  ];

  return (
    <div
      ref={containerRef}
      className="graph-explorer relative min-h-[calc(100vh-3rem)] overflow-hidden"
    >
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

      {/* 顶栏控件 */}
      <div className="absolute left-0 right-0 top-0 z-10 flex flex-wrap items-center gap-2 p-3">
        <div className="flex gap-1 rounded-lg border border-white/10 bg-slate-900/80 p-1 backdrop-blur-sm">
          {layerButtons.map((b) => (
            <button
              key={b.key}
              type="button"
              onClick={() => {
                setLayer(b.key);
                setSelectedId(null);
              }}
              className="rounded-md px-3 py-1 text-sm transition"
              style={{
                backgroundColor: layer === b.key ? `${gt.accent}26` : 'transparent',
                color: layer === b.key ? gt.accentSoft : '#94a3b8',
                fontWeight: layer === b.key ? 600 : 400,
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
        <button
          type="button"
          onClick={toggleFullscreen}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-300 backdrop-blur-sm hover:border-white/20 hover:text-white"
        >
          全屏
        </button>
        <div className="ml-auto flex gap-3 text-xs text-slate-400">
          <span>{visibleNodes.length} 地点</span>
          <span>{visibleEdges.length} 段路</span>
        </div>
      </div>

      {/* 右侧路段栏（全高，距离只在栏内显示，地图不飘字） */}
      {(layer === 'all' || layer === 'real') && routeLegs.length > 0 && (
        <aside className="absolute bottom-4 right-3 top-14 z-10 flex w-[22rem] flex-col overflow-hidden rounded-xl border border-white/10 bg-slate-900/94 shadow-xl backdrop-blur-md">
          <div className="shrink-0 border-b border-white/10 px-3 py-2.5">
            <div className="text-sm font-semibold text-slate-100">路段一览</div>
            <div className="text-xs text-slate-400">点击行高亮该段 · 悬停连线显示距离</div>
          </div>

          {activeLegEntry && activeLeg && (
            <div
              className="shrink-0 border-b border-white/10 px-3 py-2.5 text-sm"
              style={{ backgroundColor: `${gt.accent}12` }}
            >
              <div className="text-xs text-slate-400">当前路段</div>
              <div className="mt-0.5 font-medium text-slate-100">
                {activeLegEntry.from.name.replace(/^.*·/, '')}
                <span className="text-slate-500"> → </span>
                {activeLegEntry.to.name.replace(/^.*·/, '')}
              </div>
              {activeLeg.bearing && (
                <div className="mt-1 text-base font-bold text-white">
                  <span style={{ color: gt.accentSoft }}>{activeLeg.bearing}</span>
                  <span className="ml-2">{activeLeg.distanceLi} 里</span>
                  {activeLeg.distanceKm != null && (
                    <span className="ml-1 text-sm font-normal text-slate-400">（约 {activeLeg.distanceKm} km）</span>
                  )}
                </div>
              )}
            </div>
          )}

          {selectedNode && (
            <div className="shrink-0 border-b border-white/10 px-3 py-2.5">
              <div className="flex items-baseline gap-2">
                <span className="font-semibold" style={{ color: gt.accentSoft }}>
                  {selectedNode.name}
                </span>
                {selectedNode.order != null && (
                  <span className="text-xs text-slate-400">第 {selectedNode.order} 站</span>
                )}
              </div>
              <p className="mt-1 line-clamp-2 text-xs leading-snug text-slate-400">{selectedNode.summary}</p>
              <a
                href={`/${bookSlug}/l/${encodeURIComponent(selectedNode.id)}`}
                className="mt-1 inline-block text-xs hover:underline"
                style={{ color: gt.accent }}
              >
                地点详情 →
              </a>
            </div>
          )}

          <ol className="min-h-0 flex-1 overflow-y-auto px-1 py-1 text-sm">
            {routeLegs.map((leg, i) => {
              const active = activeLegKey === leg.key;
              const fromName = leg.from.name.replace(/^.*·/, '');
              const toName = leg.to.name.replace(/^.*·/, '');
              return (
                <li key={leg.key}>
                  <button
                    type="button"
                    onClick={() => {
                      setActiveLegKey((prev) => (prev === leg.key ? null : leg.key));
                      setSelectedId(leg.to.id);
                    }}
                    className="flex w-full items-center gap-2 rounded-lg px-2 py-2.5 text-left transition hover:bg-white/5"
                    style={{
                      backgroundColor: active ? `${gt.accent}18` : undefined,
                      borderLeft: active ? `3px solid ${gt.accent}` : '3px solid transparent',
                    }}
                  >
                    <span className="w-5 shrink-0 text-xs text-slate-500">{i + 1}</span>
                    <span className="min-w-0 flex-1 text-slate-200">
                      <span className="block truncate">{fromName}</span>
                      <span className="block truncate text-xs text-slate-500">→ {toName}</span>
                    </span>
                    {leg.edge?.bearing && (
                      <span className="shrink-0 text-right leading-tight">
                        <span className="block text-xs font-medium" style={{ color: gt.accentSoft }}>
                          {leg.edge.bearing}
                        </span>
                        <span className="block text-sm font-bold text-white">{leg.edge.distanceLi}里</span>
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ol>
        </aside>
      )}

      {/* 方位罗盘 */}
      <div
        className="absolute bottom-4 left-3 z-10 flex h-16 w-16 flex-col items-center justify-center rounded-lg border border-white/10 bg-slate-900/85 text-[10px] text-slate-400 backdrop-blur-md"
        aria-hidden
      >
        <span className="font-medium text-slate-300">北</span>
        <div className="flex w-full items-center justify-between px-1">
          <span>西</span>
          <span className="text-slate-600">·</span>
          <span>东</span>
        </div>
        <span>南</span>
      </div>

      {/* 区域图例 */}
      <div className="absolute bottom-4 left-20 z-10 flex max-w-[calc(100%-26rem)] flex-wrap gap-x-3 gap-y-1.5 rounded-lg border border-white/10 bg-slate-900/85 p-2.5 backdrop-blur-md">
        {realms.map((r) => (
          <span key={r} className="flex items-center gap-1.5 text-xs text-slate-300">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: realmColor(r) }} />
            {r}
          </span>
        ))}
        <span className="flex items-center gap-1.5 text-xs text-slate-500">● 凡间 · ◆ 异界</span>
      </div>

      <div ref={chartRef} className="absolute inset-0 h-full w-full" style={{ minHeight: 'calc(100vh - 3rem)' }} />

      {/* 路径方位·距离（叠在连线中点，随缩放平移） */}
      {(layer === 'all' || layer === 'real') && pathLabels.length > 0 && (
        <div className="pointer-events-none absolute inset-0 z-[5] overflow-hidden">
          {pathLabels.map((l) => (
            <div
              key={l.key}
              className="absolute whitespace-nowrap rounded-lg border px-3 py-1.5 text-[17px] font-bold leading-none text-white shadow-md"
              style={{
                left: l.x,
                top: l.y,
                transform: 'translate(-50%, -50%)',
                borderColor: gt.accent,
                backgroundColor: l.active ? 'rgba(15, 23, 42, 0.98)' : 'rgba(15, 23, 42, 0.93)',
                boxShadow: l.active ? `0 0 14px ${gt.accent}55` : undefined,
              }}
            >
              <span style={{ color: gt.accentSoft }}>{l.bearing}</span>
              <span className="ml-2">{l.distanceLi}里</span>
            </div>
          ))}
        </div>
      )}

      <p className="pointer-events-none absolute bottom-4 left-1/2 z-0 -translate-x-1/2 select-none text-center text-xs text-slate-600/70">
        右栏查全路段 · 悬停/选中连线显示距离 · 滚轮缩放
      </p>
    </div>
  );
}
