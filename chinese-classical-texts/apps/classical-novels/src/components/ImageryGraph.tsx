import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import type { ImageryGraph as GraphData } from '../lib/imagery';
import { MAPPING_PREDICATES, SHADOW_PREDICATES, SUBTYPE_LABEL, imageryBookSlugFromId } from '../lib/imagery';
import type { ImageryChain } from '../lib/imageryChains';
import { resolveChainHops } from '../lib/imageryChains';

const KIND_COLORS: Record<string, string> = {
  character: '#8f1f2b',
  myth: '#5a4a86',
  judgment: '#355766',
  poem: '#b08338',
  symbol: '#bf4c54',
  flower_lot: '#6f5347',
  name_omen: '#a8543b',
  object_omen: '#8a6d2f',
  tune_omen: '#5d7a6a',
  alchemy: '#7a5230',
  place_omen: '#3f6b54',
};

const MAPPING_COLOR = '#b08338';
const SHADOW_COLOR = '#5a4a86';
const HOT_COLOR = '#c0392b';
const COLD_COLOR = '#2c6e8f';

function edgeKindOf(predicate: string): 'mapping' | 'shadow' | 'normal' {
  if (MAPPING_PREDICATES.has(predicate)) return 'mapping';
  if (SHADOW_PREDICATES.has(predicate)) return 'shadow';
  return 'normal';
}

function neighborSet(nodeId: string, edges: GraphData['edges']): Set<string> {
  const set = new Set<string>([nodeId]);
  for (const e of edges) {
    if (e.source === nodeId) set.add(e.target);
    if (e.target === nodeId) set.add(e.source);
  }
  return set;
}

function nodeHref(bookSlug: string, node: GraphData['nodes'][0]): string {
  if (node.kind === 'character') {
    const slug = imageryBookSlugFromId(node.id) ?? bookSlug;
    if (imageryBookSlugFromId(node.id)) {
      return `/${slug}/imagery/${node.id}`;
    }
    return `/${bookSlug}/c/${encodeURIComponent(node.id)}`;
  }
  const slug = imageryBookSlugFromId(node.id) ?? bookSlug;
  return `/${slug}/imagery/${node.id}`;
}

interface Props {
  graph: GraphData;
  bookSlug: string;
  chains: ImageryChain[];
  /** ?chain= id from URL */
  initialChainId?: string | null;
}

function pathEdgeKeys(path: string[]): Set<string> {
  const keys = new Set<string>();
  for (let i = 0; i < path.length - 1; i++) {
    keys.add(`${path[i]}|${path[i + 1]}`);
    keys.add(`${path[i + 1]}|${path[i]}`);
  }
  return keys;
}

function chainIndexFromId(chains: ImageryChain[], id: string | null | undefined): number {
  if (!id) return -1;
  return chains.findIndex((c) => c.id === id);
}

export default function ImageryGraph({ graph, bookSlug, chains, initialChainId }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [chartReady, setChartReady] = useState(false);
  const [activeChain, setActiveChain] = useState(() => chainIndexFromId(chains, initialChainId));

  const activeChainDef = activeChain >= 0 ? chains[activeChain] : null;
  const activePath = activeChainDef?.path ?? [];
  const pathSet = useMemo(() => new Set(activePath), [activePath]);
  const pathEdges = useMemo(() => pathEdgeKeys(activePath), [activePath]);
  const chainHops = useMemo(
    () => (activePath.length > 1 ? resolveChainHops(activePath, graph) : []),
    [activePath, graph],
  );

  const selectedNode = selected ? graph.nodes.find((n) => n.id === selected) : null;
  const selectedEdges = useMemo(
    () =>
      selected
        ? graph.edges.filter((e) => e.source === selected || e.target === selected)
        : [],
    [graph.edges, selected],
  );

  const nodeLabel = useCallback(
    (id: string) => graph.nodes.find((n) => n.id === id)?.label ?? id,
    [graph.nodes],
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const url = new URL(window.location.href);
    if (activeChain >= 0 && chains[activeChain]?.id) {
      url.searchParams.set('chain', chains[activeChain].id);
    } else {
      url.searchParams.delete('chain');
    }
    window.history.replaceState({}, '', url);
  }, [activeChain, chains]);

  const buildOption = useCallback((): EChartsOption => {
    const categories = [...new Set(graph.nodes.map((n) => n.kind))].map((k) => ({
      name: SUBTYPE_LABEL[k] ?? k,
      itemStyle: { color: KIND_COLORS[k] ?? '#6a5c49' },
    }));

    const categoryIndex = (kind: string) =>
      categories.findIndex((c) => c.name === (SUBTYPE_LABEL[kind] ?? kind));

    const focusNeighbors = selected ? neighborSet(selected, graph.edges) : null;
    const chainFocus = activePath.length > 0 && !selected;

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(43, 28, 23, 0.92)',
        borderColor: 'rgba(143, 31, 43, 0.4)',
        textStyle: { color: '#fdf5ec', fontSize: 13 },
        formatter: (p: { dataType?: string; data?: Record<string, unknown> }) => {
          if (p.dataType === 'edge') {
            const d = p.data ?? {};
            const inf = d.inference ? '推论' : '事实';
            const phase = d.phase ? ` · ${d.phase}` : '';
            const temp = d.temperature ? `（${d.temperature}）` : '';
            return `<strong>${d.sourceLabel}</strong> — ${d.predicate}${temp} — <strong>${d.targetLabel}</strong><br/><span style="opacity:0.85">${inf}${phase}${d.note ? ' · ' + d.note : ''}</span>`;
          }
          const d = p.data ?? {};
          return `<strong>${d.displayName ?? d.name}</strong><br/>${SUBTYPE_LABEL[String(d.kind)] ?? d.kind}`;
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          draggable: true,
          focusNodeAdjacency: true,
          categories,
          force: {
            repulsion: chainFocus ? 360 : 280,
            edgeLength: chainFocus ? [80, 160] : [60, 140],
            gravity: chainFocus ? 0.06 : 0.1,
          },
          data: graph.nodes.map((n) => {
            const onPath = pathSet.has(n.id);
            const isSel = selected === n.id;
            const dimmed = chainFocus
              ? !onPath
              : focusNeighbors
                ? !focusNeighbors.has(n.id)
                : false;
            const isTaixu = n.layer === '太虚';
            return {
              id: n.id,
              name: n.label,
              displayName: n.label,
              kind: n.kind,
              symbol: isTaixu ? 'diamond' : 'circle',
              symbolSize: n.size + (onPath ? 10 : 0) + (isSel ? 10 : 0),
              category: categoryIndex(n.kind),
              itemStyle: {
                color: KIND_COLORS[n.kind],
                borderColor: isSel
                  ? '#b08338'
                  : onPath
                    ? '#e7c66b'
                    : isTaixu
                      ? '#e7c66b'
                      : 'rgba(255,255,255,0.35)',
                borderWidth: isSel ? 3 : onPath ? 2.5 : isTaixu ? 2 : 1,
                opacity: dimmed ? 0.2 : 1,
                shadowBlur: isSel ? 20 : onPath ? 16 : isTaixu ? 10 : 0,
                shadowColor: onPath ? '#e7c66b' : isTaixu ? '#e7c66b' : KIND_COLORS[n.kind],
              },
              label: {
                show: true,
                color: dimmed ? 'rgba(100,80,70,0.5)' : onPath ? '#2a1810' : '#3d2a24',
                fontSize: isSel ? 13 : onPath ? 12 : 11,
                fontWeight: isSel || onPath ? 600 : 400,
              },
            };
          }),
          links: graph.edges.map((e) => {
            const src = graph.nodes.find((n) => n.id === e.source);
            const tgt = graph.nodes.find((n) => n.id === e.target);
            const onPath =
              pathEdges.has(`${e.source}|${e.target}`) || pathEdges.has(`${e.target}|${e.source}`);
            const dimmed = chainFocus
              ? !onPath
              : focusNeighbors
                ? !(focusNeighbors.has(e.source) && focusNeighbors.has(e.target))
                : false;
            const ekind = edgeKindOf(e.predicate);
            const tempColor = e.temperature === '热' ? HOT_COLOR : e.temperature === '冷' ? COLD_COLOR : null;
            const baseColor =
              tempColor ??
              (ekind === 'mapping' ? MAPPING_COLOR : ekind === 'shadow' ? SHADOW_COLOR : e.inference ? '#355766' : '#8f1f2b');
            const baseType =
              ekind === 'shadow' ? ([3, 3] as number[]) : e.inference ? ([6, 4] as number[]) : 'solid';
            const baseWidth = tempColor ? 2.2 : ekind === 'mapping' ? 2.4 : e.inference ? 1.2 : 1.8;
            return {
              source: e.source,
              target: e.target,
              predicate: e.predicate,
              inference: e.inference,
              note: e.note,
              phase: e.phase,
              temperature: e.temperature,
              sourceLabel: src?.label ?? e.source,
              targetLabel: tgt?.label ?? e.target,
              label: {
                show: onPath,
                formatter: e.predicate,
                fontSize: 10,
                color: '#5a4038',
                backgroundColor: 'rgba(253,245,236,0.92)',
                padding: [2, 4],
                borderRadius: 3,
              },
              lineStyle: {
                type: baseType,
                width: onPath ? 3.2 : baseWidth,
                opacity: dimmed ? 0.08 : onPath ? 1 : ekind !== 'normal' ? 0.85 : e.inference ? 0.55 : 0.75,
                color: onPath ? '#b08338' : baseColor,
                curveness: ekind === 'mapping' ? 0.05 : 0.15,
              },
            };
          }),
          emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
        },
      ],
    };
  }, [graph, pathSet, pathEdges, selected, activePath.length]);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current);
    inst.current = chart;

    const onClick = (params: { dataType?: string; data?: { id?: string; name?: string } }) => {
      if (params.dataType !== 'node' || !params.data) return;
      const id = params.data.id ?? params.data.name;
      if (!id) return;
      const node = graph.nodes.find((n) => n.id === id || n.label === id);
      if (!node) return;
      setSelected((prev) => (prev === node.id ? null : node.id));
    };

    chart.on('click', onClick);
    chart.getZr().on('click', (e: { target?: unknown }) => {
      if (!e.target) setSelected(null);
    });

    setChartReady(true);
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(chartRef.current);

    return () => {
      ro.disconnect();
      chart.off('click', onClick);
      chart.dispose();
      inst.current = null;
      setChartReady(false);
    };
  }, []);

  useEffect(() => {
    if (!chartReady || !inst.current) return;
    inst.current.setOption(buildOption(), { notMerge: true });
  }, [chartReady, buildOption]);

  useEffect(() => {
    if (!chartReady || !inst.current || activePath.length === 0) return;
    const idx = graph.nodes.findIndex((n) => n.id === activePath[0]);
    if (idx >= 0) {
      inst.current.dispatchAction({ type: 'focusNodeAdjacency', dataIndex: idx });
    }
  }, [chartReady, activePath, graph.nodes]);

  return (
    <div className="relative">
      <p className="mb-2 text-xs text-muted">
        {bookSlug === 'honglou' && (
          <>
            ◆ 太虚幻境（神话层）· ● 人间贾府 ·{' '}
            <span style={{ color: MAPPING_COLOR }}>金线=投胎/还泪/投影映射</span> ·{' '}
            <span style={{ color: SHADOW_COLOR }}>紫线=影身</span> ·{' '}
          </>
        )}
        {bookSlug === 'jinpingmei' && (
          <>
            因果闭环：欲起→聚敛→极盛→反噬→散尽 ·{' '}
            <span style={{ color: HOT_COLOR }}>热线=繁华纵欲</span> ·{' '}
            <span style={{ color: COLD_COLOR }}>冷线=死亡虚无</span>（冷热金针）·{' '}
          </>
        )}
        实线=事实 · 虚线=推论 · 点击节点高亮相邻 · 选链路后非路径节点淡化
      </p>
      <div className="flex flex-col gap-3 lg:flex-row">
        <div
          ref={chartRef}
          className="min-w-0 flex-1 rounded-xl border"
          style={{
            height: 460,
            borderColor: 'var(--line)',
            background: 'color-mix(in srgb, var(--paper-2) 85%, white)',
          }}
        />
        {selectedNode && (
          <aside
            className="graph-detail-panel w-full shrink-0 rounded-xl border p-4 lg:w-72"
            style={{
              borderColor: 'var(--line)',
              background: 'var(--paper-2)',
              maxHeight: 460,
            }}
          >
            <div className="mb-3 flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="truncate text-lg font-semibold" style={{ color: 'var(--primary)' }}>
                  {selectedNode.label}
                </div>
                <div className="text-xs text-muted">
                  {SUBTYPE_LABEL[selectedNode.kind] ?? selectedNode.kind}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="shrink-0 rounded p-1 text-sm opacity-50 hover:opacity-100"
                aria-label="关闭"
              >
                ✕
              </button>
            </div>
            <ul
              className="graph-panel-scroll space-y-1.5 overflow-y-auto text-sm"
              style={{ maxHeight: 'calc(460px - 5.5rem)', color: 'var(--ink)' }}
            >
              {selectedEdges.map((e, i) => {
                const otherId = e.source === selectedNode.id ? e.target : e.source;
                const other = graph.nodes.find((n) => n.id === otherId);
                return (
                  <li key={i} className="leading-snug">
                    <span style={{ color: e.inference ? '#355766' : '#8f1f2b' }}>{e.predicate}</span>
                    <span className="text-muted"> → </span>
                    <a
                      href={other ? nodeHref(bookSlug, other) : '#'}
                      className="hover:underline"
                      style={{ color: 'var(--accent)' }}
                    >
                      {other?.label ?? otherId}
                    </a>
                    {e.inference && <span className="ml-1 text-xs text-muted">推论</span>}
                  </li>
                );
              })}
            </ul>
            <a
              href={nodeHref(bookSlug, selectedNode)}
              className="mt-3 inline-block text-sm hover:underline"
              style={{ color: 'var(--primary)' }}
            >
              查看详情 →
            </a>
          </aside>
        )}
      </div>

      {chains.length > 0 && (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted">示例链路</span>
            {chains.map((chain, i) => (
              <button
                key={chain.id}
                type="button"
                onClick={() => {
                  setActiveChain((prev) => (prev === i ? -1 : i));
                  setSelected(null);
                }}
                className="chip transition hover:opacity-90"
                style={
                  activeChain === i
                    ? {
                        borderColor: 'color-mix(in srgb, var(--primary) 55%, transparent)',
                        color: 'var(--primary)',
                        background: 'color-mix(in srgb, var(--primary) 8%, var(--paper-2))',
                        fontWeight: 600,
                      }
                    : undefined
                }
                aria-pressed={activeChain === i}
                title={chain.summary}
              >
                {chain.name}
              </button>
            ))}
            {activeChain >= 0 && (
              <button
                type="button"
                onClick={() => setActiveChain(-1)}
                className="text-xs text-muted hover:underline"
              >
                清除高亮
              </button>
            )}
          </div>

          {activeChainDef && (
            <div
              className="rounded-xl border p-4 text-sm"
              style={{ borderColor: 'var(--line)', background: 'var(--paper-2)' }}
            >
              <div className="mb-2 font-medium" style={{ color: 'var(--primary)' }}>
                {activeChainDef.name}
              </div>
              {activeChainDef.summary && (
                <p className="mb-3 text-xs leading-relaxed text-muted">{activeChainDef.summary}</p>
              )}
              <ol className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
                {activePath.map((nodeId, i) => {
                  const node = graph.nodes.find((n) => n.id === nodeId);
                  const hop = chainHops[i - 1];
                  return (
                    <li key={`${nodeId}-${i}`} className="flex flex-wrap items-center gap-1.5">
                      {i > 0 && (
                        <span
                          className="hidden text-xs text-muted sm:inline"
                          title={hop?.note}
                        >
                          {hop?.predicate ?? '·'}
                          {hop?.inference && '（推论）'}
                          {hop?.chapter != null && ` · 第${hop.chapter}回`}
                          →
                        </span>
                      )}
                      <a
                        href={node ? nodeHref(bookSlug, node) : '#'}
                        className="rounded-md px-2 py-1 text-xs ring-1 ring-white/15 hover:ring-white/30"
                        style={{
                          background: pathSet.has(nodeId)
                            ? 'color-mix(in srgb, var(--primary) 12%, transparent)'
                            : undefined,
                          color: 'var(--ink)',
                          fontWeight: 600,
                        }}
                      >
                        {i + 1}. {nodeLabel(nodeId)}
                      </a>
                    </li>
                  );
                })}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
