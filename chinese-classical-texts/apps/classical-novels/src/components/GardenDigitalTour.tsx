import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { graphTheme } from '../lib/graphTheme';
import {
  GARDEN_GUIDES,
  ZONE_COLORS,
  ZONE_LABELS,
  ZONE_ORDER,
  zoneColor,
  type GardenMapData,
  type GardenMapNode,
  type GardenZone,
} from '../lib/gardenMap';
import {
  GARDEN_DIGITAL_TOUR_EXTERIOR,
  GARDEN_DIGITAL_TOUR_PIN_NOTE,
  GARDEN_DIGITAL_TOUR_PINS,
  GARDEN_DIGITAL_TOUR_WALL,
  pinToPercent,
  pinToScene,
  type PinTier,
} from '../lib/gardenDigitalTourPins';
import { bearingLabel, logicalSteps } from '../lib/gardenSceneCoords';
import { BRIDGE_NODE_REASONS, isBridgeNode } from '../lib/bookMapCrosslinks';
import MapCrossLinks from './MapCrossLinks';

const SCENE_W = 1536;
const SCENE_H = 1024;
const PX_PER_STEP = 6;

const TIER_DOT: Record<PinTier, number> = { primary: 16, secondary: 13, minor: 10 };
const TIER_LABEL: Record<PinTier, string> = {
  primary: 'text-[11px] font-bold',
  secondary: 'text-[10px] font-semibold',
  minor: 'text-[9px] font-medium',
};

const GUIDE_COLORS: Record<string, string> = {
  ch17: '#e0b059',
  liulaolao: '#6ee7b7',
  ch23: '#93c5fd',
  ch38: '#f9a8d4',
};

interface Props {
  data: GardenMapData;
  bookSlug: string;
  baseImage: string;
}

type ZoneFilter = 'all' | GardenZone;

export default function GardenDigitalTour({ data, bookSlug, baseImage }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const shellRef = useRef<HTMLDivElement>(null);
  const [zone, setZone] = useState<ZoneFilter>('all');
  const [showTour, setShowTour] = useState(false);
  const [activeGuide, setActiveGuide] = useState<string>('ch17');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [exteriorBridgeId, setExteriorBridgeId] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [viewReady, setViewReady] = useState(false);
  const dragRef = useRef<{ px: number; py: number; ox: number; oy: number } | null>(null);
  const userMovedRef = useRef(false);

  const activeGuideMeta = useMemo(
    () => GARDEN_GUIDES.find((g) => g.key === activeGuide) ?? GARDEN_GUIDES[0],
    [activeGuide],
  );

  const guidePath = activeGuideMeta.path;

  const guideStopIndex = useMemo(() => {
    const m = new Map<string, number>();
    guidePath.forEach((id, i) => m.set(id, i + 1));
    return m;
  }, [guidePath]);

  const guideColor = GUIDE_COLORS[activeGuide] ?? gt.accent;

  const fitToView = useCallback(() => {
    if (!shellRef.current) return;
    const rect = shellRef.current.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    const fitScale = Math.min(rect.width / SCENE_W, rect.height / SCENE_H) * 0.92;
    setScale(fitScale);
    setPan({
      x: (rect.width - SCENE_W * fitScale) / 2,
      y: (rect.height - SCENE_H * fitScale) / 2,
    });
    setViewReady(true);
  }, []);

  useEffect(() => {
    const run = () => {
      if (!userMovedRef.current) fitToView();
    };
    run();
    const el = shellRef.current;
    if (!el) return;
    const ro = new ResizeObserver(run);
    ro.observe(el);
    return () => ro.disconnect();
  }, [fitToView]);

  const nodeById = useMemo(() => new Map(data.nodes.map((n) => [n.id, n])), [data.nodes]);

  const visibleNodes = useMemo(
    () => data.nodes.filter((n) => zone === 'all' || n.zone === zone),
    [data.nodes, zone],
  );

  const selected = selectedId ? (nodeById.get(selectedId) ?? null) : null;

  const focusNode = useCallback(
    (id: string) => {
      const p = pinToScene(id, SCENE_W, SCENE_H);
      if (!p || !shellRef.current) return;
      const rect = shellRef.current.getBoundingClientRect();
      const targetScale = Math.min(2.2, Math.max(1.1, scale));
      setScale(targetScale);
      setPan({
        x: rect.width / 2 - p.x * targetScale,
        y: rect.height / 2 - p.y * targetScale,
      });
      setSelectedId(id);
      setExteriorBridgeId(null);
    },
    [scale],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedId(null);
        setExteriorBridgeId(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    userMovedRef.current = true;
    const delta = e.deltaY > 0 ? 0.92 : 1.08;
    setScale((s) => Math.min(3, Math.max(0.55, s * delta)));
  };

  const onPointerDown = (e: React.PointerEvent) => {
    if ((e.target as HTMLElement).closest('[data-pin]')) return;
    userMovedRef.current = true;
    dragRef.current = { px: e.clientX, py: e.clientY, ox: pan.x, oy: pan.y };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragRef.current) return;
    setPan({
      x: dragRef.current.ox + (e.clientX - dragRef.current.px),
      y: dragRef.current.oy + (e.clientY - dragRef.current.py),
    });
  };

  const onPointerUp = () => {
    dragRef.current = null;
  };

  const tourLine = useMemo(() => {
    if (!showTour) return null;
    const pts = guidePath
      .map((id) => pinToScene(id, SCENE_W, SCENE_H))
      .filter(Boolean) as { x: number; y: number }[];
    if (pts.length < 2) return null;
    return pts.map((p) => `${p.x},${p.y}`).join(' ');
  }, [showTour, guidePath]);

  const resetView = () => {
    userMovedRef.current = false;
    fitToView();
    setSelectedId(null);
  };

  const onGuideChange = (key: string) => {
    setActiveGuide(key);
    setShowTour(true);
  };

  const distances = useMemo(() => {
    if (!selected) return [];
    return data.nodes
      .filter((n) => n.id !== selected.id)
      .map((n) => ({
        id: n.id,
        steps: logicalSteps({ x: selected.x, y: selected.y }, { x: n.x, y: n.y }, PX_PER_STEP),
        bearing: bearingLabel({ x: selected.x, y: selected.y }, { x: n.x, y: n.y }),
      }))
      .sort((a, b) => a.steps - b.steps)
      .slice(0, 6);
  }, [selected, data.nodes]);

  return (
    <div
      className="garden-digital-tour graph-explorer relative overflow-hidden bg-[#0c1210]"
      style={{ height: 'calc(100dvh - var(--graph-chrome, 3rem))', minHeight: '480px' }}
    >
      <div
        ref={shellRef}
        className="absolute inset-0 cursor-grab active:cursor-grabbing"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        <div
          className="absolute left-0 top-0 origin-top-left will-change-transform"
          style={{
            width: SCENE_W,
            height: SCENE_H,
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
            opacity: viewReady ? 1 : 0,
            transition: viewReady ? 'opacity 0.2s ease' : undefined,
          }}
        >
          <img
            src={baseImage}
            alt="大观园数字文旅鸟瞰"
            width={SCENE_W}
            height={SCENE_H}
            className="pointer-events-none block select-none"
            draggable={false}
          />

          {GARDEN_DIGITAL_TOUR_WALL && (
            <svg
              className="pointer-events-none absolute inset-0"
              width={SCENE_W}
              height={SCENE_H}
              viewBox={`0 0 ${SCENE_W} ${SCENE_H}`}
              aria-hidden
            >
              <rect
                x={(GARDEN_DIGITAL_TOUR_WALL.xMin / 100) * SCENE_W}
                y={(GARDEN_DIGITAL_TOUR_WALL.yMin / 100) * SCENE_H}
                width={((GARDEN_DIGITAL_TOUR_WALL.xMax - GARDEN_DIGITAL_TOUR_WALL.xMin) / 100) * SCENE_W}
                height={((GARDEN_DIGITAL_TOUR_WALL.yMax - GARDEN_DIGITAL_TOUR_WALL.yMin) / 100) * SCENE_H}
                fill="none"
                stroke="rgba(251,191,36,0.22)"
                strokeWidth={2}
                strokeDasharray="6 4"
                rx={4}
              />
            </svg>
          )}

          {GARDEN_DIGITAL_TOUR_EXTERIOR.map((lab) => {
            const bridge = isBridgeNode(lab.id);
            const pill = (
              <span className="whitespace-nowrap rounded-md border border-amber-500/35 bg-amber-950/88 px-2.5 py-1 text-[11px] font-semibold tracking-wide text-amber-100 shadow-lg backdrop-blur-sm">
                {lab.id}
                <span className="ml-1.5 text-[9px] font-normal text-amber-200/55">墙外</span>
              </span>
            );
            return (
              <div
                key={lab.id}
                className="pointer-events-auto absolute z-[9] -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${lab.xPct}%`, top: `${lab.yPct}%` }}
              >
                {bridge ? (
                  <button
                    type="button"
                    className="block hover:opacity-90"
                    onClick={() => {
                      setSelectedId(null);
                      setExteriorBridgeId(lab.id);
                    }}
                    title={BRIDGE_NODE_REASONS[lab.id]}
                  >
                    {pill}
                  </button>
                ) : lab.href ? (
                  <a href={lab.href} className="block hover:opacity-90">
                    {pill}
                  </a>
                ) : (
                  pill
                )}
              </div>
            );
          })}

          {tourLine && (
            <svg
              className="pointer-events-none absolute inset-0"
              width={SCENE_W}
              height={SCENE_H}
              viewBox={`0 0 ${SCENE_W} ${SCENE_H}`}
            >
              <polyline
                points={tourLine}
                fill="none"
                stroke="rgba(0,0,0,0.45)"
                strokeWidth={8}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <polyline
                points={tourLine}
                fill="none"
                stroke={guideColor}
                strokeWidth={4}
                strokeDasharray="12 8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}

          {showTour &&
            guidePath.map((id) => {
              const p = pinToScene(id, SCENE_W, SCENE_H);
              const step = guideStopIndex.get(id);
              if (!p || step == null) return null;
              return (
                <div
                  key={`tour-${id}-${activeGuide}`}
                  className="pointer-events-none absolute z-[11] flex h-6 w-6 -translate-x-[calc(50%+10px)] -translate-y-[calc(50%+12px)] items-center justify-center rounded-full text-[10px] font-bold shadow-md"
                  style={{
                    left: `${(p.x / SCENE_W) * 100}%`,
                    top: `${(p.y / SCENE_H) * 100}%`,
                    backgroundColor: guideColor,
                    color: '#0f1419',
                    border: '2px solid rgba(255,255,255,0.9)',
                  }}
                >
                  {step}
                </div>
              );
            })}

          {visibleNodes.map((n) => {
            const pos = pinToPercent(n.id);
            const pin = GARDEN_DIGITAL_TOUR_PINS[n.id];
            if (!pos || !pin) return null;
            const isSel = n.id === selectedId;
            const color = zoneColor(n.zone);
            const pinTier = pin.tier;
            const dot = TIER_DOT[pinTier];
            const labelAbove = pos.top > 72;
            const onTour = showTour && guideStopIndex.has(n.id);
            const dimmed = showTour && !onTour;

            return (
              <button
                key={n.id}
                type="button"
                data-pin
                className="absolute z-10 -translate-x-1/2 -translate-y-1/2 transition-all hover:z-20 hover:scale-110"
                style={{
                  left: `${pos.left}%`,
                  top: `${pos.top}%`,
                  opacity: dimmed ? 0.38 : 1,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setExteriorBridgeId(null);
                  setSelectedId(n.id);
                }}
                aria-label={n.name}
                aria-pressed={isSel}
                title={n.name}
              >
                <span
                  className="relative flex items-center justify-center rounded-full border-2 shadow-lg"
                  style={{
                    width: isSel ? dot + 4 : dot,
                    height: isSel ? dot + 4 : dot,
                    backgroundColor: color,
                    borderColor: isSel ? gt.accentSoft : 'rgba(255,255,255,0.9)',
                    boxShadow: isSel ? `0 0 0 4px ${gt.accent}66` : '0 2px 8px rgba(0,0,0,0.45)',
                  }}
                />
                <span
                  className={`absolute left-1/2 -translate-x-1/2 whitespace-nowrap rounded px-1.5 py-0.5 shadow-md ${TIER_LABEL[pinTier]} ${
                    labelAbove ? 'bottom-full mb-1' : 'top-full mt-1'
                  }`}
                  style={{
                    backgroundColor: isSel ? 'rgba(20, 16, 8, 0.94)' : 'rgba(10, 12, 16, 0.88)',
                    color: isSel ? gt.accentSoft : '#f1f5f9',
                    border: `1px solid ${isSel ? gt.accentLine : 'rgba(255,255,255,0.18)'}`,
                  }}
                >
                  {n.name}
                  {n.tourOrder != null && (
                    <span className="ml-0.5 opacity-75">·{n.tourOrder}</span>
                  )}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div
        className="pointer-events-none absolute left-3 top-3 z-20 rounded-lg border px-3 py-2 shadow-xl backdrop-blur-md"
        style={{
          borderColor: `${gt.accent}66`,
          backgroundColor: 'rgba(10, 14, 18, 0.88)',
        }}
      >
        <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400">Digital Culture Tourism</div>
        <div className="text-lg font-bold" style={{ color: gt.accentSoft }}>
          大观园数字文旅
        </div>
        <div className="mt-0.5 max-w-[220px] text-xs leading-snug text-slate-400">
          园内标注 · 墙外琥珀色为两府接点
        </div>
      </div>

      <div className="absolute right-3 top-3 z-20 flex flex-wrap items-center justify-end gap-2">
        <select
          value={zone}
          onChange={(e) => setZone(e.target.value as ZoneFilter)}
          className="rounded-lg border border-white/15 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 backdrop-blur-md"
        >
          <option value="all">全部分区</option>
          {ZONE_ORDER.filter((z) => data.nodes.some((n) => n.zone === z)).map((z) => (
            <option key={z} value={z}>
              {ZONE_LABELS[z]}
            </option>
          ))}
        </select>
        <select
          value={activeGuide}
          onChange={(e) => onGuideChange(e.target.value)}
          className="rounded-lg border border-white/15 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 backdrop-blur-md"
          aria-label="导览路线"
          title="切换不同回目的叙事游线，地图上显示带序号的虚线路径"
        >
          {GARDEN_GUIDES.map((g) => (
            <option key={g.key} value={g.key}>
              导览 · {g.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 rounded-lg border border-white/15 bg-slate-900/90 px-3 py-2 text-sm text-slate-200 backdrop-blur-md">
          <input
            type="checkbox"
            checked={showTour}
            onChange={(e) => setShowTour(e.target.checked)}
            className="accent-amber-400"
          />
          导览线
        </label>
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/15 bg-slate-900/90 px-3 py-2 text-sm text-slate-200 backdrop-blur-md hover:bg-slate-800/90"
        >
          复位
        </button>
      </div>

      {showTour && (
        <div
          className="absolute left-1/2 top-14 z-20 max-w-[min(96%,720px)] -translate-x-1/2 rounded-lg border px-3 py-2 text-center text-xs shadow-lg backdrop-blur-md"
          style={{
            borderColor: `${guideColor}55`,
            backgroundColor: 'rgba(10, 14, 18, 0.9)',
            color: '#e2e8f0',
          }}
        >
          <span className="font-semibold" style={{ color: guideColor }}>
            {activeGuideMeta.label}
          </span>
          <span className="text-slate-500"> · 第{activeGuideMeta.chapter}回 · </span>
          <span className="text-slate-400">{guidePath.join(' → ')}</span>
        </div>
      )}

      {exteriorBridgeId && !selected && (
        <div className="absolute right-3 top-[4.5rem] z-20 w-72 rounded-xl border border-amber-500/25 bg-slate-900/92 p-4 shadow-xl backdrop-blur-md">
          <h3 className="text-lg font-bold text-amber-100">{exteriorBridgeId}</h3>
          <p className="mt-1 text-xs text-amber-200/70">{BRIDGE_NODE_REASONS[exteriorBridgeId]}</p>
          <MapCrossLinks
            bookSlug={bookSlug}
            current="digital-tour"
            nodeId={exteriorBridgeId}
            size="sm"
            className="mt-3"
          />
          <button
            type="button"
            className="mt-3 text-xs text-slate-500 hover:text-slate-300"
            onClick={() => setExteriorBridgeId(null)}
          >
            关闭
          </button>
        </div>
      )}

      {selected && (
        <div className="absolute right-3 top-[4.5rem] z-20 max-h-[calc(100%-8rem)] w-72 overflow-y-auto rounded-xl border border-white/15 bg-slate-900/92 p-4 shadow-xl backdrop-blur-md">
          <h3 className="text-xl font-bold" style={{ color: gt.accentSoft }}>
            {selected.name}
          </h3>
          {selected.plaque && (
            <p className="mt-1 text-xs text-slate-400">匾 · {selected.plaque}</p>
          )}
          <p className="mt-1 text-xs" style={{ color: ZONE_COLORS[selected.zone] }}>
            {ZONE_LABELS[selected.zone]}
            {selected.tourOrder != null && ` · 第17回游线第 ${selected.tourOrder} 站`}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-slate-300">{selected.summary}</p>
          {distances.length > 0 && (
            <>
              <p className="mt-4 text-xs font-medium text-slate-500">到其他建筑（逻辑步数）</p>
              <ul className="mt-1 space-y-1 text-xs text-slate-300">
                {distances.map((d) => (
                  <li key={d.id} className="flex justify-between gap-2">
                    <button
                      type="button"
                      className="text-left hover:underline"
                      style={{ color: gt.accentSoft }}
                      onClick={() => focusNode(d.id)}
                    >
                      {d.id}
                      <span className="text-slate-500"> {d.bearing}</span>
                    </button>
                    <span className="shrink-0 text-slate-400">约 {d.steps} 步</span>
                  </li>
                ))}
              </ul>
            </>
          )}
          <div className="mt-4 flex flex-wrap gap-2">
            <a
              href={`/${bookSlug}/l/${encodeURIComponent(selected.id)}`}
              className="rounded-md border border-white/20 px-3 py-1.5 text-xs text-slate-200 hover:bg-white/10"
            >
              词条 →
            </a>
          </div>
          <MapCrossLinks
            bookSlug={bookSlug}
            current="digital-tour"
            nodeId={selected.id}
            className="mt-3 border-t border-white/10 pt-3"
          />
        </div>
      )}

      <p className="pointer-events-none absolute bottom-3 left-3 z-10 max-w-md text-[10px] leading-relaxed text-slate-500">
        {GARDEN_DIGITAL_TOUR_PIN_NOTE.slice(0, 42)}… · 滚轮缩放 · 拖拽平移
      </p>
    </div>
  );
}
