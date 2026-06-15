import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ImageryGraph as GraphData } from '../lib/imagery';
import { HIGHLIGHT_CHAINS, SUBTYPE_LABEL } from '../lib/imagery';

const KIND_COLORS: Record<string, string> = {
  character: '#8f1f2b',
  judgment: '#355766',
  poem: '#b08338',
  symbol: '#bf4c54',
  flower_lot: '#6f5347',
};

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
    return `/${bookSlug}/c/${encodeURIComponent(node.id)}`;
  }
  return `/${bookSlug}/imagery/${node.id}`;
}

interface Props {
  graph: GraphData;
  bookSlug: string;
  /** @deprecated 链路切换已内置，保留兼容默认高亮第一条 */
  highlightPath?: string[];
}

function pathEdgeKeys(path: string[]): Set<string> {
  const keys = new Set<string>();
  for (let i = 0; i < path.length - 1; i++) {
    keys.add(`${path[i]}|${path[i + 1]}`);
    keys.add(`${path[i + 1]}|${path[i]}`);
  }
  return keys;
}

export default function ImageryGraph({ graph, bookSlug, highlightPath }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [chartReady, setChartReady] = useState(false);
  const [activeChain, setActiveChain] = useState(() => {
    if (!highlightPath?.length) return 0;
    const idx = HIGHLIGHT_CHAINS.findIndex(
      (c) => c.path.length === highlightPath.length && c.path.every((id, i) => id === highlightPath[i]),
    );
    return idx >= 0 ? idx : 0;
  });

  const activePath = activeChain >= 0 ? HIGHLIGHT_CHAINS[activeChain]?.path ?? [] : [];
  const pathSet = useMemo(() => new Set(activePath), [activePath]);
  const pathEdges = useMemo(() => pathEdgeKeys(activePath), [activePath]);

  const selectedNode = selected ? graph.nodes.find((n) => n.id === selected) : null;
  const selectedEdges = useMemo(
    () =>
      selected
        ? graph.edges.filter((e) => e.source === selected || e.target === selected)
        : [],
    [graph.edges, selected],
  );

  const buildOption = useCallback((): EChartsOption => {
    const categories = [...new Set(graph.nodes.map((n) => n.kind))].map((k) => ({
      name: SUBTYPE_LABEL[k] ?? k,
      itemStyle: { color: KIND_COLORS[k] ?? '#6a5c49' },
    }));

    const categoryIndex = (kind: string) =>
      categories.findIndex((c) => c.name === (SUBTYPE_LABEL[kind] ?? kind));

    const focusNeighbors = selected ? neighborSet(selected, graph.edges) : null;

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
            return `<strong>${d.sourceLabel}</strong> — ${d.predicate} — <strong>${d.targetLabel}</strong><br/><span style="opacity:0.85">${inf}${d.note ? ' · ' + d.note : ''}</span>`;
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
          force: { repulsion: 280, edgeLength: [60, 140], gravity: 0.1 },
          data: graph.nodes.map((n) => {
            const onPath = pathSet.has(n.id);
            const isSel = selected === n.id;
            const dimmed = focusNeighbors ? !focusNeighbors.has(n.id) : false;
            return {
              id: n.id,
              name: n.label,
              displayName: n.label,
              kind: n.kind,
              symbolSize: n.size + (onPath ? 8 : 0) + (isSel ? 10 : 0),
              category: categoryIndex(n.kind),
              itemStyle: {
                color: KIND_COLORS[n.kind],
                borderColor: isSel ? '#b08338' : onPath ? '#b08338' : 'rgba(255,255,255,0.35)',
                borderWidth: isSel ? 3 : onPath ? 2 : 1,
                opacity: dimmed ? 0.25 : 1,
                shadowBlur: isSel ? 20 : onPath ? 12 : 0,
                shadowColor: KIND_COLORS[n.kind],
              },
              label: {
                show: true,
                color: dimmed ? 'rgba(100,80,70,0.5)' : '#3d2a24',
                fontSize: isSel ? 13 : 11,
                fontWeight: isSel ? 600 : 400,
              },
            };
          }),
          links: graph.edges.map((e) => {
            const src = graph.nodes.find((n) => n.id === e.source);
            const tgt = graph.nodes.find((n) => n.id === e.target);
            const onPath =
              pathEdges.has(`${e.source}|${e.target}`) || pathEdges.has(`${e.target}|${e.source}`);
            const dimmed = focusNeighbors
              ? !(focusNeighbors.has(e.source) && focusNeighbors.has(e.target))
              : false;
            return {
              source: e.source,
              target: e.target,
              predicate: e.predicate,
              inference: e.inference,
              note: e.note,
              sourceLabel: src?.label ?? e.source,
              targetLabel: tgt?.label ?? e.target,
              label: { show: false, formatter: e.predicate, fontSize: 10 },
              lineStyle: {
                type: e.inference ? [6, 4] : 'solid',
                width: onPath ? 2.5 : e.inference ? 1.2 : 1.8,
                opacity: dimmed ? 0.12 : onPath ? 0.95 : e.inference ? 0.55 : 0.75,
                color: e.inference ? '#355766' : '#8f1f2b',
                curveness: 0.15,
              },
            };
          }),
          emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
        },
      ],
    };
  }, [graph, pathSet, pathEdges, selected]);

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

  return (
    <div className="relative">
      <p className="mb-2 text-xs" style={{ color: 'var(--ink-soft)' }}>
        实线 = 事实关联 · 虚线 = 推论（隐喻/影射/预示）· 点击节点高亮相邻
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
                <div className="text-xs" style={{ color: 'var(--ink-soft)' }}>
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
                    <span style={{ color: 'var(--ink-soft)' }}> → </span>
                    <a
                      href={other ? nodeHref(bookSlug, other) : '#'}
                      className="hover:underline"
                      style={{ color: 'var(--accent)' }}
                    >
                      {other?.label ?? otherId}
                    </a>
                    {e.inference && (
                      <span className="ml-1 text-[10px]" style={{ color: 'var(--ink-soft)' }}>
                        推论
                      </span>
                    )}
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

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs" style={{ color: 'var(--ink-soft)' }}>
          示例链路
        </span>
        {HIGHLIGHT_CHAINS.map((chain, i) => (
          <button
            key={chain.name}
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
          >
            {chain.name}
          </button>
        ))}
        {activeChain >= 0 && (
          <button
            type="button"
            onClick={() => setActiveChain(-1)}
            className="text-xs hover:underline"
            style={{ color: 'var(--ink-soft)' }}
          >
            清除高亮
          </button>
        )}
      </div>
    </div>
  );
}
