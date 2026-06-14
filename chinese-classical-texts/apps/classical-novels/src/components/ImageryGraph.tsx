import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ImageryGraph as GraphData } from '../lib/imagery';
import { SUBTYPE_LABEL } from '../lib/imagery';

const KIND_COLORS: Record<string, string> = {
  character: '#8f1f2b',
  judgment: '#355766',
  poem: '#b08338',
  symbol: '#bf4c54',
  flower_lot: '#6f5347',
};

interface Props {
  graph: GraphData;
  bookSlug: string;
  highlightPath?: string[];
}

export default function ImageryGraph({ graph, bookSlug, highlightPath }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const pathSet = useMemo(() => new Set(highlightPath ?? []), [highlightPath]);

  const option = useMemo((): EChartsOption => {
    const categories = [...new Set(graph.nodes.map((n) => n.kind))].map((k) => ({
      name: SUBTYPE_LABEL[k] ?? k,
      itemStyle: { color: KIND_COLORS[k] ?? '#6a5c49' },
    }));

    const categoryIndex = (kind: string) => categories.findIndex((c) => c.name === (SUBTYPE_LABEL[kind] ?? kind));

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(43, 28, 23, 0.92)',
        borderColor: 'rgba(143, 31, 43, 0.4)',
        textStyle: { color: '#fdf5ec', fontSize: 13 },
        formatter: (p: any) => {
          if (p.dataType === 'edge') {
            const inf = p.data.inference ? '推论' : '事实';
            return `<strong>${p.data.sourceLabel}</strong> — ${p.data.predicate} — <strong>${p.data.targetLabel}</strong><br/><span style="opacity:0.85">${inf}${p.data.note ? ' · ' + p.data.note : ''}</span>`;
          }
          return `<strong>${p.data.label}</strong><br/>${SUBTYPE_LABEL[p.data.kind] ?? p.data.kind}`;
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
            return {
              id: n.id,
              name: n.id,
              label: n.label,
              kind: n.kind,
              symbolSize: n.size + (onPath ? 8 : 0) + (isSel ? 6 : 0),
              category: categoryIndex(n.kind),
              itemStyle: {
                color: KIND_COLORS[n.kind],
                borderColor: onPath ? '#b08338' : 'transparent',
                borderWidth: onPath ? 3 : 0,
              },
            };
          }),
          links: graph.edges.map((e) => {
            const src = graph.nodes.find((n) => n.id === e.source);
            const tgt = graph.nodes.find((n) => n.id === e.target);
            const onPath =
              pathSet.size > 0 &&
              pathSet.has(e.source) &&
              pathSet.has(e.target);
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
                opacity: onPath ? 0.95 : e.inference ? 0.55 : 0.75,
                color: e.inference ? '#355766' : '#8f1f2b',
                curveness: 0.15,
              },
            };
          }),
          emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
        },
      ],
    };
  }, [graph, pathSet, selected]);

  useEffect(() => {
    if (!chartRef.current) return;
    if (!inst.current) {
      inst.current = echarts.init(chartRef.current);
      inst.current.on('click', (p: any) => {
        if (p.dataType === 'node') setSelected((prev) => (prev === p.data.id ? null : p.data.id));
      });
    }
    inst.current.setOption(option, true);
    const ro = new ResizeObserver(() => inst.current?.resize());
    ro.observe(chartRef.current);
    return () => {
      ro.disconnect();
      inst.current?.dispose();
      inst.current = null;
    };
  }, [option]);

  return (
    <div>
      <p className="mb-2 text-xs" style={{ color: 'var(--ink-soft)' }}>
        实线 = 事实关联 · 虚线 = 推论（隐喻/影射/预示）· 点击节点高亮相邻
      </p>
      <div
        ref={chartRef}
        className="w-full rounded-xl border"
        style={{
          height: 460,
          borderColor: 'var(--line)',
          background: 'color-mix(in srgb, var(--paper-2) 85%, white)',
        }}
      />
    </div>
  );
}
