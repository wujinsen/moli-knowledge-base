import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { echarts, type EChartsOption } from '../lib/echartsCore';
import { graphTheme } from '../lib/graphTheme';
import {
  GARDEN_CHAPTER_PRESETS,
  GARDEN_GUIDES,
  ZONE_COLORS,
  ZONE_LABELS,
  ZONE_ORDER,
  buildGardenEdges,
  zoneColor,
  type GardenMapData,
  type GardenMapNode,
  type GardenZone,
} from '../lib/gardenMap';
import { GARDEN_LAYOUT_DISCLAIMER } from '../lib/gardenSceneCoords';
import GardenZoneCatalog from './GardenZoneCatalog';
import MapCrossLinks from './MapCrossLinks';

interface Props {
  data: GardenMapData;
  bookSlug: string;
}

type ZoneFilter = 'all' | GardenZone;

export default function GardenMap({ data, bookSlug }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const [zone, setZone] = useState<ZoneFilter>('all');
  const [showTour, setShowTour] = useState(true);
  const [showCatalog, setShowCatalog] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [chapterFilter, setChapterFilter] = useState<number | null>(null);
  const [activeGuide, setActiveGuide] = useState<string | null>(null);

  const guidePath = useMemo(() => {
    if (activeGuide !== 'liulaolao') return null;
    return GARDEN_GUIDES.find((g) => g.key === 'liulaolao')?.path ?? null;
  }, [activeGuide]);

  const allEdges = useMemo(
    () => buildGardenEdges(data.nodes, guidePath),
    [data.nodes, guidePath],
  );

  const nodeById = useMemo(
    () => new Map(data.nodes.map((n) => [n.id, n])),
    [data.nodes],
  );

  const zones = useMemo(
    () => ZONE_ORDER.filter((z) => data.nodes.some((n) => n.zone === z)),
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
      allEdges.filter((e) => {
        if (!visibleIds.has(e.source) || !visibleIds.has(e.target)) return false;
        if (e.kind === 'tour' && !showTour) return false;
        if (e.kind === 'guide' && !activeGuide) return false;
        return true;
      }),
    [allEdges, visibleIds, showTour, activeGuide],
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
        textStyle: { color: '#e2e8f0', fontSize: 14, fontFamily: '"Noto Serif SC", serif', fontWeight: 500 },
        formatter: (p: unknown) => {
          const params = p as { dataType?: string; data?: Record<string, unknown> };
          if (params.dataType === 'edge') return '';
          const node = nodeById.get((params.data?.id as string) ?? '');
          if (!node) return '';
          const tour = node.tourOrder != null ? `<br/>第17回游线 · 第 ${node.tourOrder} 站` : '';
          const ch = node.chapters.length
            ? `<br/><span style="color:${gt.accent}">第${node.chapters.slice(0, 3).join('、')}${node.chapters.length > 3 ? '…' : ''}回</span>`
            : '';
          return `<strong style="font-size:17px;font-weight:700">${node.name}</strong><br/>${ZONE_LABELS[node.zone]}${tour}${ch}`;
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
            const dimmed =
              chapterFilter != null && !n.chapters.includes(chapterFilter);
            const hasEvent =
              chapterFilter != null &&
              n.events.some((ev) => ev.chapters.includes(chapterFilter));
            const size =
              n.zone === '仪典' ? 30 : n.zone === '路径' ? 18 : n.zone === '水系' ? 24 : 26;
            const symbol =
              n.zone === '居所'
                ? 'roundRect'
                : n.zone === '水系'
                  ? 'diamond'
                  : n.zone === '仪典'
                    ? 'pin'
                    : n.zone === '寺观'
                      ? 'triangle'
                      : 'circle';
            return {
              id: n.id,
              name: n.name,
              x: n.x,
              y: n.y,
              symbol,
              symbolSize: selected ? size * 1.35 : hasEvent ? size * 1.15 : size,
              itemStyle: {
                color,
                opacity: dimmed ? 0.28 : 1,
                borderColor: selected
                  ? '#fff'
                  : hasEvent
                    ? '#fcd34d'
                    : 'rgba(255,255,255,0.35)',
                borderWidth: selected ? 2.5 : hasEvent ? 2.2 : 1.2,
                shadowBlur: selected ? 28 : hasEvent ? 18 : 12,
                shadowColor: hasEvent ? '#fcd34d' : color,
              },
              label: {
                show: true,
                position: 'bottom',
                distance: 8,
                color: selected ? '#fff' : dimmed ? 'rgba(241,245,249,0.45)' : '#f1f5f9',
                fontSize: selected ? 17 : 15,
                fontWeight: selected ? 700 : 600,
                fontFamily: '"Noto Serif SC", "Songti SC", serif',
              },
            };
          }),
          edges: visibleEdges.map((e) => ({
            source: e.source,
            target: e.target,
            symbol: e.kind !== 'nearby' ? ['none', 'arrow'] : ['none', 'none'],
            symbolSize: e.kind === 'nearby' ? 0 : e.kind === 'guide' ? [0, 9] : [0, 8],
            lineStyle: {
              color:
                e.kind === 'guide'
                  ? '#4ade80'
                  : e.kind === 'tour'
                    ? '#fbbf24'
                    : 'rgba(148,163,184,0.55)',
              width: e.kind === 'guide' ? 3 : e.kind === 'tour' ? 2.5 : 1.2,
              type: e.kind === 'nearby' ? 'solid' : 'dashed',
              opacity: e.kind === 'nearby' ? 0.45 : 0.88,
              curveness: e.kind === 'guide' ? 0.02 : e.kind === 'tour' ? 0.04 : 0.1,
            },
          })),
        },
      ],
    };
  }, [visibleNodes, visibleEdges, selectedId, nodeById, gt, chapterFilter]);

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
    setShowTour(true);
    setChapterFilter(null);
    setActiveGuide(null);
    chartInstance.current?.dispatchAction({ type: 'restore' });
  };

  const activateGuide = (key: string) => {
    const g = GARDEN_GUIDES.find((x) => x.key === key);
    if (!g) return;
    if (key === 'ch17') {
      setActiveGuide(null);
      setChapterFilter(17);
      setShowTour(true);
      return;
    }
    setActiveGuide((prev) => (prev === key ? null : key));
    setChapterFilter(g.chapter);
    setShowTour(false);
  };

  const zoneButtons: { key: ZoneFilter; label: string }[] = [
    { key: 'all', label: '全部' },
    ...zones.map((z) => ({ key: z as ZoneFilter, label: ZONE_LABELS[z] })),
  ];

  return (
    <div
      ref={containerRef}
      className="garden-map graph-explorer relative min-h-[calc(100vh-3rem)] overflow-hidden"
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
              className="rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
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
          <span className="text-sm font-medium text-slate-400">回目</span>
          <select
            value={chapterFilter ?? ''}
            onChange={(e) => {
              const v = e.target.value;
              setChapterFilter(v === '' ? null : Number(v));
              setActiveGuide(null);
            }}
            className="max-w-[11rem] rounded-md border-0 bg-transparent py-1 text-sm font-medium text-slate-100 outline-none"
          >
            {GARDEN_CHAPTER_PRESETS.map((p) => (
              <option key={p.label} value={p.chapter ?? ''} className="bg-slate-900">
                {p.label}
              </option>
            ))}
          </select>
        </label>
        {GARDEN_GUIDES.map((g) => {
          const active =
            g.key === 'ch17'
              ? chapterFilter === 17 && showTour && activeGuide == null
              : activeGuide === g.key;
          return (
          <button
            key={g.key}
            type="button"
            onClick={() => activateGuide(g.key)}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium backdrop-blur-sm hover:border-white/20"
            style={{
              borderColor: active
                ? g.key === 'ch17'
                  ? 'rgba(251,191,36,0.5)'
                  : 'rgba(74,222,128,0.55)'
                : undefined,
              color: active
                ? g.key === 'ch17'
                  ? '#fcd34d'
                  : '#86efac'
                : '#e2e8f0',
            }}
          >
            {g.label}
          </button>
          );
        })}
        <button
          type="button"
          onClick={() => setShowCatalog((v) => !v)}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/20 hover:text-white"
          style={{
            borderColor: showCatalog ? `${gt.accent}66` : undefined,
            color: showCatalog ? gt.accentSoft : undefined,
          }}
        >
          {showCatalog ? '隐藏名录' : '建筑名录'}
        </button>
        <button
          type="button"
          onClick={() => setShowTour((v) => !v)}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/20 hover:text-white"
          style={{
            borderColor: showTour ? 'rgba(251,191,36,0.5)' : undefined,
            color: showTour ? '#fcd34d' : undefined,
          }}
        >
          {showTour ? '隐藏游线' : '显示游线'}
        </button>
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/20 hover:text-white"
        >
          重置视图
        </button>
        <div className="ml-auto flex gap-3 text-sm font-medium text-slate-300">
          <span>{visibleNodes.length} 处</span>
          <span>{visibleEdges.length} 条边</span>
        </div>
      </div>

      <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-sm rounded-lg border border-amber-500/25 bg-slate-900/85 px-3 py-2 backdrop-blur-md">
        <p className="text-xs leading-relaxed text-amber-100/90">{GARDEN_LAYOUT_DISCLAIMER}</p>
      </div>

      <div className="absolute bottom-4 left-3 z-10 max-w-lg flex flex-wrap gap-x-4 gap-y-2 rounded-lg border border-white/10 bg-slate-900/85 p-3 backdrop-blur-md">
        {zones.map((z) => (
          <span key={z} className="flex items-center gap-2 text-sm font-medium text-slate-200">
            <span className="inline-block h-3 w-3 rounded-full" style={{ backgroundColor: ZONE_COLORS[z] }} />
            {ZONE_LABELS[z]}
          </span>
        ))}
        <span className="text-sm text-slate-400">
          虚线黄 = 第17回游线 · 虚线绿 = 导览线 · 实线 = 邻近
          {chapterFilter != null && ' · 淡色 = 该回未出场'}
        </span>
      </div>

      <div
        className="absolute bottom-4 right-3 z-10 flex h-[4.5rem] w-[4.5rem] flex-col items-center justify-center rounded-lg border border-white/10 bg-slate-900/85 text-xs font-medium text-slate-300 backdrop-blur-md"
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

      {showCatalog && (
        <GardenZoneCatalog
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
          className="garden-map-panel absolute right-3 top-16 z-10 max-h-[calc(100vh-6rem)] w-80 overflow-y-auto rounded-xl border bg-slate-900/90 p-5 shadow-xl backdrop-blur-md"
          style={{ borderColor: gt.accentLine }}
        >
          <div className="mb-1 text-xl font-bold" style={{ color: gt.accentSoft }}>
            {selectedNode.name}
          </div>
          <div className="mb-3 text-sm font-medium text-slate-300">
            {ZONE_LABELS[selectedNode.zone]}
            {selectedNode.category ? ` · ${selectedNode.category}` : ''}
            {selectedNode.tourOrder != null && ` · 游线第 ${selectedNode.tourOrder} 站`}
          </div>

          {selectedNode.plaque && (
            <div className="mb-2 text-base font-medium" style={{ color: gt.accentSoft }}>
              匾 · {selectedNode.plaque}
            </div>
          )}
          {selectedNode.couplet && (
            <div className="mb-3 text-sm leading-relaxed text-slate-300">
              {selectedNode.couplet.upper}；{selectedNode.couplet.lower}
            </div>
          )}

          <p className="mb-4 text-base leading-relaxed text-slate-200">{selectedNode.summary}</p>

          {selectedNode.events.length > 0 && (
            <div className="mb-4">
              <div className="mb-1.5 text-sm font-semibold text-slate-400">关联大事</div>
              <div className="flex flex-col gap-1.5">
                {selectedNode.events.map((ev) => (
                  <a
                    key={ev.id}
                    href={`/${bookSlug}/e/${ev.id}`}
                    className="rounded border border-white/10 px-2.5 py-1.5 text-sm font-medium text-slate-200 hover:border-white/25 hover:bg-white/5"
                  >
                    {ev.title}
                    <span className="ml-1 text-xs text-slate-400">
                      第{ev.chapters.join('、')}回
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {selectedNode.occupants.length > 0 && (
            <div className="mb-4">
              <div className="mb-1.5 text-sm font-semibold text-slate-400">住客</div>
              <div className="flex flex-wrap gap-1.5">
                {selectedNode.occupants.map((o) => (
                  <a
                    key={o}
                    href={`/${bookSlug}/c/${encodeURIComponent(o)}`}
                    className="rounded px-2 py-1 text-sm font-medium hover:underline"
                    style={{ backgroundColor: `${gt.accent}1a`, color: gt.accentSoft }}
                  >
                    {o}
                  </a>
                ))}
              </div>
            </div>
          )}

          {selectedNode.plants.length > 0 && (
            <div className="mb-4 text-sm text-slate-300">植物：{selectedNode.plants.join('、')}</div>
          )}

          {selectedNode.chapters.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-1.5">
              {selectedNode.chapters.slice(0, 8).map((c) => (
                <a
                  key={c}
                  href={`/${bookSlug}/read/${c}`}
                  className="rounded border border-white/10 px-2 py-1 text-sm text-slate-200 hover:border-white/30 hover:text-white"
                >
                  第{c}回
                </a>
              ))}
            </div>
          )}

          <div className="flex flex-col gap-2.5">
            <a
              href={`/${bookSlug}/l/${encodeURIComponent(selectedNode.id)}`}
              className="text-base font-medium hover:underline"
              style={{ color: gt.accent }}
            >
              地点详情 →
            </a>
            <a
              href={`/${bookSlug}/topics/大观园游线与间数摘录`}
              className="text-sm text-slate-400 hover:text-slate-200"
            >
              第17回游线考证
            </a>
            <MapCrossLinks
              bookSlug={bookSlug}
              current="garden"
              nodeId={selectedNode.id}
              size="sm"
            />
            <a href={`/${bookSlug}/places`} className="text-sm text-slate-400 hover:text-slate-200">
              建筑图鉴
            </a>
          </div>
        </aside>
      )}

      <div ref={chartRef} className="absolute inset-0 h-full w-full" style={{ minHeight: 'calc(100vh - 3rem)' }} />

      <p className="pointer-events-none absolute bottom-20 left-1/2 z-0 max-w-2xl -translate-x-1/2 select-none px-4 text-center text-xs leading-relaxed text-slate-500">
        滚轮缩放 · 点击地点 ·{' '}
        <a
          href={`/${bookSlug}/topics/大观园游线与间数摘录`}
          className="pointer-events-auto underline decoration-dotted underline-offset-2 hover:text-slate-300"
        >
          第17回游线 fact 与 inference 分层说明
        </a>
      </p>
    </div>
  );
}
