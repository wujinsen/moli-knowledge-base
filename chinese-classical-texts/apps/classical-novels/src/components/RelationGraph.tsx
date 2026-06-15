import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import { factionColor, relationColor, graphTheme } from '../lib/graphTheme';
import { relationGraphForSlug } from '../lib/relations';

interface Node {
  id: string;
  type: string;
  faction: string;
  weight?: number;
  chapter?: number;
  summary?: string;
  variantIds?: string[];
}
interface Edge {
  source: string;
  target: string;
  type: string;
  contradiction?: boolean;
  inference?: boolean;
}
interface Props {
  bookSlug: string;
}

function neighborSet(nodeId: string, edges: Edge[]): Set<string> {
  const set = new Set<string>([nodeId]);
  for (const e of edges) {
    if (e.source === nodeId) set.add(e.target);
    if (e.target === nodeId) set.add(e.source);
  }
  return set;
}

function circularCoords(index: number, total: number, radius = 280): { x: number; y: number } {
  const angle = (2 * Math.PI * index) / Math.max(total, 1);
  return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius };
}

function forceSettings(nodeCount: number) {
  return {
    initLayout: 'circular' as const,
    repulsion: Math.min(420, Math.max(100, 6500 / nodeCount)),
    gravity: 0.14,
    edgeLength: nodeCount > 80 ? [45, 110] : [70, 150],
    friction: 0.42,
  };
}

export default function RelationGraph({ bookSlug }: Props) {
  const data = useMemo(() => relationGraphForSlug(bookSlug), [bookSlug]);
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const layoutPositionsRef = useRef<Map<string, { x: number; y: number }>>(new Map());
  const prevPhysicsRef = useRef(true);

  const [chartReady, setChartReady] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hiddenFactions, setHiddenFactions] = useState<Set<string>>(new Set());
  const [physics, setPhysics] = useState(true);
  const [expandedEdgeTypes, setExpandedEdgeTypes] = useState<Set<string>>(new Set());

  useEffect(() => {
    const focus = new URLSearchParams(window.location.search).get('focus');
    if (focus && data.nodes.some((n) => n.id === focus)) {
      setSelectedId(focus);
      setQuery(focus);
      setHiddenFactions(new Set());
    }
  }, [data.nodes]);

  const factions = useMemo(
    () => [...new Set(data.nodes.map((n) => n.faction))],
    [data.nodes],
  );

  const visibleNodes = useMemo(
    () => data.nodes.filter((n) => !hiddenFactions.has(n.faction)),
    [data.nodes, hiddenFactions],
  );
  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);
  const visibleEdges = useMemo(
    () => data.edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [data.edges, visibleIds],
  );

  const selectedNode = selectedId ? data.nodes.find((n) => n.id === selectedId) : null;
  const selectedEdges = useMemo(
    () =>
      selectedId
        ? visibleEdges.filter((e) => e.source === selectedId || e.target === selectedId)
        : [],
    [selectedId, visibleEdges],
  );

  const groupedSelectedEdges = useMemo(() => {
    if (!selectedNode) return [];
    const map = new Map<
      string,
      { target: string; inference?: boolean; contradiction?: boolean }[]
    >();
    for (const e of selectedEdges) {
      const other = e.source === selectedNode.id ? e.target : e.source;
      if (!map.has(e.type)) map.set(e.type, []);
      map.get(e.type)!.push({
        target: other,
        inference: e.inference,
        contradiction: e.contradiction,
      });
    }
    return [...map.entries()]
      .map(([type, items]) => ({
        type,
        items: [...items].sort((a, b) => a.target.localeCompare(b.target, 'zh-CN')),
      }))
      .sort((a, b) => b.items.length - a.items.length);
  }, [selectedEdges, selectedNode]);

  useEffect(() => {
    if (!selectedId) {
      setExpandedEdgeTypes(new Set());
      return;
    }
    const edges = visibleEdges.filter((e) => e.source === selectedId || e.target === selectedId);
    const typeCounts = new Map<string, number>();
    for (const e of edges) {
      typeCounts.set(e.type, (typeCounts.get(e.type) ?? 0) + 1);
    }
    const auto = new Set<string>();
    for (const [type, count] of typeCounts) {
      if (count <= 4) auto.add(type);
    }
    if (auto.size === 0) {
      const top = [...typeCounts.entries()].sort((a, b) => b[1] - a[1])[0];
      if (top) auto.add(top[0]);
    }
    setExpandedEdgeTypes(auto);
  }, [selectedId, visibleEdges]);

  const toggleEdgeType = (type: string) => {
    setExpandedEdgeTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  const buildOption = useCallback((): EChartsOption => {
    const focusNeighbors = selectedId ? neighborSet(selectedId, visibleEdges) : null;
    const q = query.trim().toLowerCase();

    const categories = factions.map((f, i) => ({
      name: f,
      itemStyle: { color: factionColor(i) },
    }));

    return {
      backgroundColor: 'transparent',
      animation: true,
      animationDuration: 1200,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(15, 23, 42, 0.92)',
        borderColor: gt.accentLine,
        borderWidth: 1,
        textStyle: { color: '#e2e8f0', fontSize: 13 },
        formatter: (p: unknown) => {
          const params = p as { dataType?: string; data?: Record<string, unknown> };
          if (params.dataType === 'edge') {
            const d = params.data ?? {};
            const tags = [d.inference ? '推论' : null, d.contradiction ? '矛盾' : null]
              .filter(Boolean)
              .join(' · ');
            return `<strong>${d.source}</strong> — ${d.label ?? d.type} — <strong>${d.target}</strong>${tags ? `<br/><span style="color:${gt.accent}">${tags}</span>` : ''}`;
          }
          const d = params.data ?? {};
          if (d.nodeType === 'topic') {
            const hint =
              bookSlug === 'jinpingmei'
                ? '词话/崇祯/竹坡版本差异'
                : '脂评/探佚与程高本分歧';
            const summary = d.summary ? `<br/>${d.summary}` : '';
            return `<strong style="font-size:15px">${d.name}</strong><br/><span style="color:${gt.accent}">版本异文议题</span><br/>${hint}${summary}`;
          }
          return `<strong style="font-size:15px">${d.name}</strong><br/>阵营：${d.faction ?? '—'}<br/>类型：${d.nodeType === 'monster' ? '妖怪' : '人物'}`;
        },
      },
      legend: {
        show: false,
      },
      series: [
        {
          type: 'graph',
          layout: physics ? 'force' : 'none',
          roam: true,
          draggable: true,
          zoom: 1.1,
          focusNodeAdjacency: true,
          emphasis: {
            focus: 'adjacency',
            scale: 1.15,
            lineStyle: { width: 3, opacity: 1 },
            itemStyle: { shadowBlur: 28 },
          },
          force: physics
            ? { ...forceSettings(visibleNodes.length), layoutAnimation: true }
            : { layoutAnimation: false },
          categories,
          data: visibleNodes.map((n, idx) => {
            const fi = factions.indexOf(n.faction);
            const color = factionColor(fi);
            const matched = q && n.id.toLowerCase().includes(q);
            const dimmed =
              (focusNeighbors && !focusNeighbors.has(n.id)) ||
              (q && !matched);
            const highlighted = q && matched;
            const size = 22 + (n.weight ?? 30) * 0.45;

            const saved = layoutPositionsRef.current.get(n.id);
            const fixedPos = !physics
              ? (saved ?? circularCoords(idx, visibleNodes.length))
              : null;

            return {
              id: n.id,
              name: n.id,
              category: fi,
              faction: n.faction,
              nodeType: n.type,
              summary: n.summary,
              chapter: n.chapter,
              ...(fixedPos ? { x: fixedPos.x, y: fixedPos.y, fixed: true } : {}),
              symbol:
                n.type === 'monster' ? 'diamond' : n.type === 'topic' ? 'roundRect' : 'circle',
              symbolSize: highlighted ? size * 1.2 : size,
              itemStyle: {
                color,
                borderColor: highlighted ? gt.accentSoft : 'rgba(255,255,255,0.35)',
                borderWidth: highlighted ? 3 : 1.5,
                shadowBlur: dimmed ? 4 : highlighted ? 32 : 18,
                shadowColor: color,
                opacity: dimmed ? 0.22 : 1,
              },
              label: {
                show: true,
                position: 'bottom',
                distance: 6,
                color: dimmed ? 'rgba(148,163,184,0.5)' : '#f1f5f9',
                fontSize: highlighted ? 14 : 12,
                fontWeight: highlighted ? 600 : 400,
              },
            };
          }),
          edges: visibleEdges.map((e) => {
            const color = relationColor(e.type);
            const dimmed = focusNeighbors
              ? !(focusNeighbors.has(e.source) && focusNeighbors.has(e.target))
              : false;
            const isInference = e.inference || e.contradiction;

            return {
              source: e.source,
              target: e.target,
              type: e.type,
              inference: e.inference,
              contradiction: e.contradiction,
              lineStyle: {
                color: isInference ? gt.accent : color,
                width: dimmed ? 0.6 : isInference ? 2 : 1.8,
                opacity: dimmed ? 0.12 : 0.75,
                curveness: 0.22,
                type: isInference ? 'dashed' : 'solid',
              },
              label: {
                show: !dimmed && visibleEdges.length <= 40,
                formatter: e.type,
                fontSize: 14,
                color: 'rgba(203,213,225,0.85)',
                backgroundColor: 'rgba(15,23,42,0.65)',
                padding: [2, 4],
                borderRadius: 3,
              },
              emphasis: {
                lineStyle: { width: 4, opacity: 1 },
              },
            };
          }),
        },
      ],
    };
  }, [factions, physics, query, selectedId, visibleEdges, visibleNodes, gt]);

  useEffect(() => {
    const el = chartRef.current;
    const container = containerRef.current;
    if (!el) return;

    let chart: echarts.ECharts | null = null;
    let cancelled = false;
    let attempts = 0;
    let rafId = 0;
    setChartError(null);

    const mountChart = () => {
      if (cancelled || chart) return;
      if (el.clientWidth < 16 || el.clientHeight < 16) {
        attempts += 1;
        if (attempts > 240) {
          setChartError('图谱画布高度为 0，请刷新页面或点击全屏');
          return;
        }
        cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(mountChart);
        return;
      }
      try {
        chart = echarts.init(el, undefined, { renderer: 'canvas' });
      } catch (err) {
        setChartError(err instanceof Error ? err.message : '图谱初始化失败');
        return;
      }
      chartInstance.current = chart;

      chart.on('click', (params) => {
        if (params.dataType === 'node' && params.data && typeof params.data === 'object') {
          const id = (params.data as { id?: string; name?: string }).id ?? (params.data as { name?: string }).name;
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
      if (!chart) mountChart();
      else chart.resize();
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mount once; data updates via effect below
  }, []);

  useEffect(() => {
    if (!chartReady || !chartInstance.current) return;
    const chart = chartInstance.current;
    const switchedToForce = !prevPhysicsRef.current && physics;
    prevPhysicsRef.current = physics;

    if (switchedToForce) chart.clear();
    chart.setOption(buildOption(), { notMerge: true });

    const timer = window.setTimeout(() => chart.resize(), switchedToForce ? 150 : 0);
    return () => clearTimeout(timer);
  }, [chartReady, buildOption, physics]);

  const captureLayoutPositions = () => {
    const chart = chartInstance.current;
    if (!chart) return;
    try {
      const seriesModel = chart.getModel().getSeriesByIndex(0);
      if (!seriesModel) return;
      const graphData = seriesModel.getData();
      const next = new Map<string, { x: number; y: number }>();
      for (let i = 0; i < graphData.count(); i++) {
        const layout = graphData.getItemLayout(i);
        if (layout && Number.isFinite(layout[0]) && Number.isFinite(layout[1])) {
          next.set(String(graphData.getName(i)), { x: layout[0], y: layout[1] });
        }
      }
      if (next.size > 0) layoutPositionsRef.current = next;
    } catch {
      /* chart mid-update */
    }
  };

  const togglePhysics = () => {
    if (physics) {
      captureLayoutPositions();
      setPhysics(false);
      return;
    }
    layoutPositionsRef.current.clear();
    setPhysics(true);
  };

  const toggleFaction = (f: string) => {
    setHiddenFactions((prev) => {
      const next = new Set(prev);
      if (next.has(f)) next.delete(f);
      else next.add(f);
      return next;
    });
    setSelectedId(null);
  };

  const resetView = () => {
    setQuery('');
    setSelectedId(null);
    setHiddenFactions(new Set());
    chartInstance.current?.dispatchAction({ type: 'restore' });
  };

  const toggleFullscreen = () => {
    const el = containerRef.current;
    if (!el) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else el.requestFullscreen();
  };

  const relationTypes = [...new Set(visibleEdges.map((e) => e.type))];
  const graphHeight = 'calc(100dvh - var(--graph-chrome, 10.5rem))';

  if (data.nodes.length === 0) {
    return (
      <div
        className="flex h-full min-h-[50vh] flex-col items-center justify-center px-4 text-center text-slate-400"
        style={{ minHeight: graphHeight }}
      >
        <p className="mb-2 text-lg" style={{ color: gt.accentSoft }}>
          关系图谱待生成
        </p>
        <p className="max-w-md text-sm">
          运行 <code className="mx-1 rounded px-2 py-0.5 bg-slate-900/80">python scripts/build_relations.py</code>{' '}
          后刷新页面。
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="graph-explorer"
      style={{ height: graphHeight, minHeight: graphHeight }}
    >
      {/* 背景装饰 */}
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{ background: gt.backdrop }}
      />
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
      <div className="graph-toolbar absolute left-0 right-0 top-0 z-10 flex h-12 items-center gap-2 px-3">
        <input
          type="search"
          placeholder="搜索人物…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-40 rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-500 backdrop-blur-sm focus:border-white/40 focus:outline-none sm:w-44"
        />
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-300 backdrop-blur-sm hover:border-white/20 hover:text-white"
        >
          重置
        </button>
        <button
          type="button"
          onClick={togglePhysics}
          className="hidden rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-300 backdrop-blur-sm hover:border-white/20 hover:text-white sm:inline-block"
        >
          {physics ? '固定布局' : '力导向'}
        </button>
        <button
          type="button"
          onClick={toggleFullscreen}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3 py-1.5 text-sm text-slate-300 backdrop-blur-sm hover:border-white/20 hover:text-white"
        >
          全屏
        </button>
        {!selectedNode && (
          <div className="ml-auto graph-stat-pill">
            <strong style={{ color: gt.accentSoft }}>{visibleNodes.length}</strong>
            <span>节点</span>
            <span className="text-slate-600">·</span>
            <strong style={{ color: gt.accentSoft }}>{visibleEdges.length}</strong>
            <span>关系</span>
          </div>
        )}
      </div>

      {/* 阵营筛选 */}
      <div className="absolute bottom-4 left-3 z-10 flex max-w-[70%] flex-wrap gap-1.5">
        {factions.map((f, i) => {
          const off = hiddenFactions.has(f);
          const color = factionColor(i);
          return (
            <button
              key={f}
              type="button"
              onClick={() => toggleFaction(f)}
              className="rounded-full border px-2.5 py-1 text-xs backdrop-blur-sm transition"
              style={{
                borderColor: off ? 'rgba(255,255,255,0.1)' : `${color}88`,
                backgroundColor: off ? 'rgba(15,23,42,0.5)' : `${color}22`,
                color: off ? '#64748b' : color,
                opacity: off ? 0.55 : 1,
              }}
            >
              {f}
            </button>
          );
        })}
      </div>

      {/* 关系图例（选中节点时改由侧栏分组展示，避免与详情面板叠盖） */}
      {relationTypes.length > 0 && !selectedNode && (
        <div className="graph-legend absolute bottom-4 right-3 z-10 max-h-32 overflow-y-auto rounded-lg border border-white/10 bg-slate-900/85 p-2 backdrop-blur-md">
          <div className="mb-1 text-xs uppercase tracking-wide text-slate-500">关系类型</div>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {relationTypes.map((t) => (
              <span key={t} className="flex items-center gap-1 text-xs text-slate-300">
                <span
                  className="inline-block h-0.5 w-4 rounded"
                  style={{ backgroundColor: relationColor(t) }}
                />
                {t}
              </span>
            ))}
          </div>
          <div className="mt-2 border-t border-white/5 pt-2 text-xs text-slate-500">
            虚线 = 推论 / 矛盾
          </div>
        </div>
      )}

      <div ref={chartRef} className="absolute inset-0 z-[1] h-full w-full" />

      {/* 选中详情（置于 canvas 之后，确保可点击） */}
      {selectedNode && (
        <aside
          className="graph-detail-panel pointer-events-auto absolute right-3 top-[3.25rem] z-30 flex w-80 flex-col rounded-xl border bg-slate-900/92 shadow-2xl backdrop-blur-md sm:w-96"
          style={{
            borderColor: gt.accentLine,
            height: 'calc(100vh - 5.5rem)',
            maxHeight: 'calc(100vh - 5.5rem)',
          }}
        >
          <div className="shrink-0 border-b border-white/5 px-4 py-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="truncate text-lg font-semibold" style={{ color: gt.accentSoft }}>
                  {selectedNode.id}
                </div>
                <div className="mt-0.5 text-xs text-slate-400">
                  {selectedNode.type === 'topic'
                    ? bookSlug === 'jinpingmei'
                      ? '词话 · 崇祯 · 竹坡 异文'
                      : '脂评 · 程高 版本争议'
                    : `${selectedNode.faction} · ${selectedNode.type === 'monster' ? '妖怪' : '人物'}`}
                </div>
                {selectedNode.type === 'topic' && selectedNode.summary && (
                  <p className="mt-2 text-xs leading-relaxed text-slate-400">{selectedNode.summary}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setSelectedId(null)}
                className="shrink-0 rounded-md p-1 text-slate-500 hover:bg-white/5 hover:text-slate-200"
                aria-label="关闭详情"
              >
                ✕
              </button>
            </div>
            <div className="graph-stat-pill mt-2.5 w-fit text-[11px]">
              <strong style={{ color: gt.accentSoft }}>{selectedEdges.length}</strong>
              <span>条邻接</span>
              <span className="text-slate-600">·</span>
              <strong style={{ color: gt.accentSoft }}>{groupedSelectedEdges.length}</strong>
              <span>类关系</span>
            </div>
          </div>
          <div className="graph-panel-scroll min-h-0 flex-1 overflow-y-auto px-3 py-2 text-sm text-slate-200">
            {groupedSelectedEdges.length === 0 ? (
              <p className="px-2 py-4 text-center text-xs text-slate-500">暂无邻接关系</p>
            ) : (
              groupedSelectedEdges.map((group) => {
              const open = expandedEdgeTypes.has(group.type);
              const color = relationColor(group.type);
              return (
                <div key={group.type} className="mb-1.5 rounded-lg border border-white/5 bg-slate-950/40">
                  <button
                    type="button"
                    onClick={() => toggleEdgeType(group.type)}
                    className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-white/5"
                  >
                    <span
                      className="inline-block h-0.5 w-3 shrink-0 rounded"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-medium" style={{ color }}>
                      {group.type}
                    </span>
                    <span className="ml-auto text-xs text-slate-500">{group.items.length}</span>
                    <span className="text-xs text-slate-500" aria-hidden>
                      {open ? '▾' : '▸'}
                    </span>
                  </button>
                  {open && (
                    <ul className="space-y-0.5 border-t border-white/5 px-3 py-2">
                      {group.items.map((item) => (
                        <li key={`${group.type}-${item.target}`} className="leading-snug">
                          <a
                            href={`/${bookSlug}/c/${encodeURIComponent(item.target)}`}
                            className="text-slate-200 hover:text-white hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {item.target}
                          </a>
                          {(item.inference || item.contradiction) && (
                            <span className="ml-1 text-xs text-slate-500">
                              {item.contradiction ? '矛盾' : '推论'}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })
            )}
            {selectedEdges.length > 12 && (
              <p className="px-1 py-2 text-center text-xs text-slate-500">
                点击关系类型展开/收起 · 侧栏可滚动
              </p>
            )}
          </div>
          {selectedNode.type === 'topic' && selectedNode.chapter ? (
            <div className="shrink-0 space-y-2 border-t border-white/5 px-4 py-3">
              <a
                href={`/${bookSlug}/compare/cihua-chongzhen/${selectedNode.chapter}`}
                className="inline-block text-sm hover:underline"
                style={{ color: gt.accent }}
              >
                对勘第 {selectedNode.chapter} 回 →
              </a>
              <a
                href={`/${bookSlug}/graph`}
                className="block text-xs text-slate-500 hover:text-slate-300"
              >
                返回全图
              </a>
            </div>
          ) : selectedNode.type !== 'topic' ? (
            <div className="shrink-0 border-t border-white/5 px-4 py-3">
              <a
                href={`/${bookSlug}/c/${encodeURIComponent(selectedNode.id)}`}
                className="inline-block text-sm hover:underline"
                style={{ color: gt.accent }}
              >
                查看人物页 →
              </a>
            </div>
          ) : null}
        </aside>
      )}

      {chartError && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-2 bg-slate-950/80 px-4 text-center text-sm text-slate-300">
          <p>图谱渲染失败：{chartError}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-lg border border-white/15 px-3 py-1.5 hover:border-white/30"
          >
            重新加载
          </button>
        </div>
      )}

      <p className="pointer-events-none absolute left-1/2 top-1/2 z-0 -translate-x-1/2 -translate-y-1/2 select-none text-center text-slate-700/40 text-sm">
        拖拽节点 · 滚轮缩放 · 点击高亮邻接
      </p>
    </div>
  );
}
