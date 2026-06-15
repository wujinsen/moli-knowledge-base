import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
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
}

type ZoneFilter = 'all' | TownZone;

export default function TownMap({ data, bookSlug }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const [zone, setZone] = useState<ZoneFilter>('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);

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
            const size = n.id === '西门府' || n.id === '清河县' ? 28 : inManor ? 18 : 20;
            return {
              id: n.id,
              name: n.name,
              x: n.x,
              y: n.y,
              symbol: inManor && n.parent ? 'roundRect' : n.zone === '寺观' ? 'diamond' : 'circle',
              symbolSize: selected ? size * 1.3 : size,
              itemStyle: {
                color,
                borderColor: selected ? '#fff' : 'rgba(255,255,255,0.35)',
                borderWidth: selected ? 2.5 : 1.2,
                shadowBlur: selected ? 28 : 12,
                shadowColor: color,
              },
              label: {
                show: true,
                position: 'bottom',
                distance: 6,
                color: selected ? '#fff' : '#e8eef7',
                fontSize: selected ? 13 : 11,
                fontWeight: selected ? 600 : 400,
              },
            };
          }),
          edges: visibleEdges.map((e) => ({
            source: e.source,
            target: e.target,
            lineStyle: {
              color: e.kind === 'parent' ? 'rgba(212,160,23,0.45)' : gt.accent,
              width: e.kind === 'parent' ? 1 : 1.5,
              type: e.kind === 'parent' ? 'dashed' : 'solid',
              opacity: 0.65,
              curveness: 0.08,
            },
          })),
        },
      ],
    };
  }, [visibleNodes, visibleEdges, selectedId, nodeById, gt]);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = echarts.init(chartRef.current, undefined, { renderer: 'canvas' });
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
    setZone('all');
    chartInstance.current?.dispatchAction({ type: 'restore' });
  };

  const zoneButtons: { key: ZoneFilter; label: string }[] = [
    { key: 'all', label: '全部' },
    ...zones.map((z) => ({ key: z as ZoneFilter, label: ZONE_LABELS[z] })),
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
          className="absolute right-3 top-16 z-10 max-h-[calc(100vh-6rem)] w-64 overflow-y-auto rounded-xl border bg-slate-900/90 p-4 shadow-xl backdrop-blur-md"
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

      <div ref={chartRef} className="absolute inset-0 h-full w-full" style={{ minHeight: 'calc(100vh - 3rem)' }} />

      <p className="pointer-events-none absolute bottom-4 left-1/2 z-0 -translate-x-1/2 select-none text-center text-xs text-slate-600/70">
        清河 · 西门府 · 东京政商链 · 滚轮缩放 · 点击地点
      </p>
    </div>
  );
}
