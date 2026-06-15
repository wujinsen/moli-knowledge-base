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

  const prevSegment = useMemo(() => {
    if (!selectedId) return null;
    const idx = routePath.findIndex((n) => n.id === selectedId);
    if (idx <= 0) return null;
    const edge = edgeByKey.get(`${routePath[idx - 1].id}→${routePath[idx].id}`);
    return edge ?? null;
  }, [selectedId, routePath, edgeByKey]);

  const nextSegment = useMemo(() => {
    if (!selectedId) return null;
    const idx = routePath.findIndex((n) => n.id === selectedId);
    if (idx < 0 || idx >= routePath.length - 1) return null;
    const edge = edgeByKey.get(`${routePath[idx].id}→${routePath[idx + 1].id}`);
    return edge ?? null;
  }, [selectedId, routePath, edgeByKey]);

  const selectedNode = selectedId ? nodeById.get(selectedId) ?? null : null;

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

  /** 选中节点时高亮其前后路段 */
  const highlightedLegKeys = useMemo(() => {
    const keys = new Set<string>();
    if (activeLegKey) keys.add(activeLegKey);
    if (selectedId) {
      const idx = routePath.findIndex((n) => n.id === selectedId);
      if (idx > 0) keys.add(`${routePath[idx - 1].id}→${routePath[idx].id}`);
      if (idx >= 0 && idx < routePath.length - 1)
        keys.add(`${routePath[idx].id}→${routePath[idx + 1].id}`);
    }
    return keys;
  }, [activeLegKey, selectedId, routePath]);

  const buildOption = useCallback((): EChartsOption => {
    return {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 900,
      animationEasing: 'cubicOut',
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
            return `<strong>${from}</strong> → ${to}<br/><span style="color:${gt.accent};font-size:15px">${meta.bearing} · ${meta.distanceLi ?? '?'} 里</span>${meta.distanceKm != null ? `<span style="color:#94a3b8">（约 ${meta.distanceKm} km）</span>` : ''}`;
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
          labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' },
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
            const meta = edgeByKey.get(key);
            const legIdx = routeLegOrder.get(key);
            const isHighlight = highlightedLegKeys.has(key);
            const segText =
              meta?.bearing && meta.distanceLi != null
                ? `${meta.bearing}  ${meta.distanceLi}里`
                : '';
            return {
              source: e.source,
              target: e.target,
              symbol: ['none', 'arrow'],
              symbolSize: [0, isHighlight ? 9 : 7],
              label: segText
                ? {
                    show: isHighlight,
                    formatter: segText,
                    rotate: 0,
                    position: 'middle',
                    align: 'center',
                    verticalAlign: 'middle',
                    fontSize: 13,
                    fontWeight: 700,
                    color: '#fff',
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    borderColor: gt.accent,
                    borderWidth: 1,
                    padding: [4, 8],
                    borderRadius: 6,
                  }
                : { show: false },
              lineStyle: {
                color: isHighlight ? gt.accentSoft : gt.accent,
                width: isHighlight ? 3.5 : 2,
                opacity: isHighlight ? 1 : 0.55,
                curveness: legIdx != null ? (legIdx % 2 === 0 ? 0.16 : -0.16) : 0.04,
              },
              emphasis: {
                lineStyle: { width: 4, opacity: 1 },
                label: segText
                  ? {
                      show: true,
                      formatter: segText,
                      rotate: 0,
                      fontSize: 13,
                      fontWeight: 700,
                      color: '#fff',
                      backgroundColor: 'rgba(15, 23, 42, 0.95)',
                      borderColor: gt.accent,
                      borderWidth: 1,
                      padding: [4, 8],
                      borderRadius: 6,
                    }
                  : { show: false },
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
          setActiveLegKey(null);
        }
      }
      if (params.dataType === 'edge' && params.data && typeof params.data === 'object') {
        const src = (params.data as { source?: string }).source;
        const tgt = (params.data as { target?: string }).target;
        if (src && tgt) setActiveLegKey(`${src}→${tgt}`);
      }
    });
    chart.getZr().on('click', (e) => {
      if (!e.target) {
        setSelectedId(null);
        setActiveLegKey(null);
      }
    });

    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
      chartInstance.current = null;
    };
  }, []);

  useEffect(() => {
    chartInstance.current?.setOption(buildOption(), { notMerge: true });
  }, [buildOption]);

  const resetView = () => {
    setSelectedId(null);
    setActiveLegKey(null);
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

      {/* 路段一览（避免地图上标签折叠） */}
      {(layer === 'all' || layer === 'real') && routeLegs.length > 0 && (
        <aside className="absolute left-3 top-14 z-10 flex w-72 max-h-[min(420px,calc(100vh-10rem))] flex-col overflow-hidden rounded-xl border border-white/10 bg-slate-900/92 shadow-xl backdrop-blur-md">
          <div className="border-b border-white/10 px-3 py-2">
            <div className="text-sm font-semibold text-slate-100">路段一览</div>
            <div className="text-xs text-slate-400">点击行高亮该段 · 悬停路线亦显示</div>
          </div>
          <ol className="flex-1 overflow-y-auto px-1 py-1 text-sm">
            {routeLegs.map((leg, i) => {
              const active = highlightedLegKeys.has(leg.key);
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
                    className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-white/5"
                    style={{
                      backgroundColor: active ? `${gt.accent}18` : undefined,
                      borderLeft: active ? `3px solid ${gt.accent}` : '3px solid transparent',
                    }}
                  >
                    <span className="w-5 shrink-0 text-xs text-slate-500">{i + 1}</span>
                    <span className="min-w-0 flex-1 truncate text-slate-200">
                      {fromName}
                      <span className="text-slate-500"> → </span>
                      {toName}
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
        className="absolute bottom-4 right-3 z-10 flex h-16 w-16 flex-col items-center justify-center rounded-lg border border-white/10 bg-slate-900/85 text-[10px] text-slate-400 backdrop-blur-md"
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
      <div className="absolute bottom-4 left-3 z-10 flex max-w-[calc(100%-20rem)] flex-wrap gap-x-3 gap-y-1.5 rounded-lg border border-white/10 bg-slate-900/85 p-2.5 backdrop-blur-md xl:max-w-[50%]">
        {realms.map((r) => (
          <span key={r} className="flex items-center gap-1.5 text-xs text-slate-300">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: realmColor(r) }} />
            {r}
          </span>
        ))}
        <span className="flex items-center gap-1.5 text-xs text-slate-500">● 凡间 · ◆ 异界</span>
      </div>

      {/* 选中详情 */}
      {selectedNode && (
        <aside
          className="absolute right-3 top-16 z-10 w-64 rounded-xl border bg-slate-900/90 p-4 shadow-xl backdrop-blur-md"
          style={{ borderColor: gt.accentLine }}
        >
          <div className="mb-1 flex items-baseline gap-2">
            <span className="text-lg font-semibold" style={{ color: gt.accentSoft }}>
              {selectedNode.name}
            </span>
            {selectedNode.order != null && (
              <span className="text-xs text-slate-400">第 {selectedNode.order} 站</span>
            )}
          </div>
          <div className="mb-2 text-xs text-slate-400">
            {selectedNode.realm} · {selectedNode.layer === 'real' ? '凡间路线' : '神话异界'}
            {selectedNode.aliases.length > 0 && <> · 又称 {selectedNode.aliases.join('、')}</>}
          </div>
          <p className="mb-3 text-sm leading-snug text-slate-300">{selectedNode.summary}</p>

          {(prevSegment || nextSegment) && (
            <div className="mb-3 space-y-2 rounded-lg border border-white/15 bg-slate-800/60 p-3 text-sm text-slate-200">
              {prevSegment?.bearing && (
                <div>
                  自上一站：
                  <span className="ml-1 font-semibold" style={{ color: gt.accentSoft }}>
                    {prevSegment.bearing}
                  </span>
                  {prevSegment.distanceLi != null && (
                    <span className="ml-1 text-base font-bold text-white">
                      {prevSegment.distanceLi} 里
                    </span>
                  )}
                  {prevSegment.distanceKm != null && (
                    <span className="text-slate-400">（约 {prevSegment.distanceKm} km）</span>
                  )}
                </div>
              )}
              {nextSegment?.bearing && (
                <div>
                  往下一站：
                  <span className="ml-1 font-semibold" style={{ color: gt.accentSoft }}>
                    {nextSegment.bearing}
                  </span>
                  {nextSegment.distanceLi != null && (
                    <span className="ml-1 text-base font-bold text-white">
                      {nextSegment.distanceLi} 里
                    </span>
                  )}
                  {nextSegment.distanceKm != null && (
                    <span className="text-slate-400">（约 {nextSegment.distanceKm} km）</span>
                  )}
                </div>
              )}
            </div>
          )}

          {selectedNode.tribulations.length > 0 && (
            <div className="mb-3">
              <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">途经劫难</div>
              <div className="flex flex-wrap gap-1">
                {selectedNode.tribulations.map((t) => (
                  <a
                    key={t.id}
                    href={`/${bookSlug}/e/${t.id}`}
                    className="rounded px-1.5 py-0.5 text-xs hover:underline"
                    style={{ backgroundColor: `${gt.accent}1a`, color: gt.accentSoft }}
                  >
                    第{t.no}难 {t.title}
                  </a>
                ))}
              </div>
            </div>
          )}

          {selectedNode.chapters.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-1">
              {selectedNode.chapters.map((c) => (
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

          <a
            href={`/${bookSlug}/l/${encodeURIComponent(selectedNode.id)}`}
            className="inline-block text-sm hover:underline"
            style={{ color: gt.accent }}
          >
            查看地点详情 →
          </a>
        </aside>
      )}

      <div ref={chartRef} className="absolute inset-0 h-full w-full" style={{ minHeight: 'calc(100vh - 3rem)' }} />

      <p className="pointer-events-none absolute bottom-4 left-1/2 z-0 -translate-x-1/2 select-none text-center text-xs text-slate-600/70">
        左栏查路段距离 · 悬停路线显示 · 滚轮缩放 · 点击地点
      </p>
    </div>
  );
}
