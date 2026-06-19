import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import L from '../lib/leafletClient';
import {
  GIS_FULL_HUBS,
  GIS_REMOTE_LABELS,
  ZONE_COLORS,
  ZONE_LABELS,
  baseGisMarkerRadius,
  buildTownGisEdges,
  filterTownGisCoreNodes,
  zoneColor,
  type TownGisMeta,
  type TownMapData,
  type TownMapNode,
  toLeafletLatLng,
} from '../lib/townMap';

interface Props {
  data: TownMapData;
  gis: TownGisMeta;
  bookSlug: string;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  initialRouteId?: string | null;
}

type GisExtent = 'core' | 'full';

type MarkerMeta = {
  node: TownMapNode;
  marker: L.CircleMarker;
};

const MIN_CONTAINER = 48;
const FIT_PADDING: [number, number] = [28, 28];

function latLngBoundsFor(nodes: TownMapNode[]) {
  return L.latLngBounds(nodes.map((n) => toLeafletLatLng(n.x, n.y)));
}

function boundsForMode(mode: GisExtent, coreNodes: TownMapNode[], allNodes: TownMapNode[]) {
  return latLngBoundsFor(mode === 'core' ? coreNodes : allNodes);
}

export default function TownLeafletMap({ data, gis, bookSlug, selectedId, onSelect, initialRouteId = null }: Props) {
  const elRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const edgeLayerRef = useRef<L.LayerGroup | null>(null);
  const markersRef = useRef<MarkerMeta[]>([]);
  const anchorZoomRef = useRef(0);
  const extentRef = useRef<GisExtent>('core');
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const selectedIdRef = useRef(selectedId);
  selectedIdRef.current = selectedId;

  const [extent, setExtent] = useState<GisExtent>('core');
  const [mapError, setMapError] = useState<string | null>(null);
  extentRef.current = extent;

  const routes = data.routes ?? [];
  const [ready, setReady] = useState(false);
  const [activeRouteId, setActiveRouteId] = useState<string | null>(
    initialRouteId && routes.some((r) => r.id === initialRouteId) ? initialRouteId : null,
  );
  const activeRouteIdRef = useRef<string | null>(null);
  activeRouteIdRef.current = activeRouteId;
  const routeLayerRef = useRef<L.LayerGroup | null>(null);
  const activeRoute = activeRouteId ? routes.find((r) => r.id === activeRouteId) ?? null : null;

  const { height, width } = gis.bounds;
  const gisEdges = useMemo(() => buildTownGisEdges(data.nodes), [data.nodes]);
  const coreNodes = useMemo(() => filterTownGisCoreNodes(data.nodes), [data.nodes]);
  const coreIds = useMemo(() => new Set(coreNodes.map((n) => n.id)), [coreNodes]);

  const applyVisuals = useCallback(
    (map: L.Map, mode: GisExtent, selected: string | null) => {
      const isFull = mode === 'full';

      edgeLayerRef.current?.eachLayer((layer) => {
        (layer as L.Polyline).setStyle?.({ opacity: isFull ? 0 : 0.5 });
      });

      for (const { node, marker } of markersRef.current) {
        const isHub = node.id === '西门府' || node.id === '清河县';
        const isRemote = node.zone === '城外' && !coreIds.has(node.id);

        let visible = true;
        let radius = baseGisMarkerRadius(node, coreIds);
        let showLabel = isHub;

        if (isFull) {
          if (node.zone === '府内') {
            visible = false;
          } else if (node.zone === '城外') {
            radius = GIS_REMOTE_LABELS.has(node.id) ? 11 : 8;
            showLabel = true;
          } else if (GIS_FULL_HUBS.has(node.id)) {
            radius = isHub ? 12 : 8;
            showLabel = true;
          } else {
            visible = false;
          }
        } else if (node.zone !== '府内') {
          // 清河详图：除密集的府内簇（悬停显示）外，其余点常显名字
          showLabel = true;
        }

        marker.setStyle({
          radius: visible ? radius : 0,
          weight: node.id === selected ? 2.5 : 1.2,
          color: node.id === selected ? '#fff' : '#0f172a',
          fillColor: zoneColor(node.zone),
          fillOpacity: visible ? (isRemote && !isFull ? 0.55 : 0.92) : 0,
        });

        const tip = marker.getTooltip();
        if (!tip) continue;
        tip.options.permanent = showLabel;
        if (showLabel && visible) marker.openTooltip();
        else marker.closeTooltip();
      }
    },
    [coreIds],
  );

  const setupMapView = useCallback(
    (map: L.Map, mode: GisExtent, animate = false) => {
      const bounds = boundsForMode(mode, coreNodes, data.nodes);
      const padRatio = mode === 'core' ? 0.05 : 0.07;

      map.fitBounds(bounds.pad(padRatio), {
        animate,
        duration: animate ? 0.35 : 0,
        padding: FIT_PADDING,
      });

      const anchor = map.getZoom();
      anchorZoomRef.current = anchor;
      map.setMinZoom(anchor);
      map.setMaxZoom(anchor + (mode === 'core' ? 2.5 : 1.5));
      map.setMaxBounds(bounds.pad(mode === 'core' ? 0.14 : 0.1));

      // fitBounds 已设置视图并投影各 marker（_point 就绪），此后 setStyle 才安全
      viewReadyRef.current = true;
      applyVisuals(map, mode, selectedIdRef.current);
      setReady(true);
    },
    [applyVisuals, coreNodes, data.nodes],
  );
  const setupMapViewRef = useRef(setupMapView);
  setupMapViewRef.current = setupMapView;
  const extentReadyRef = useRef(false);
  const viewReadyRef = useRef(false);

  useEffect(() => {
    const el = elRef.current;
    if (!el || data.nodes.length === 0) return;

    viewReadyRef.current = false;
    setReady(false);
    let map: L.Map | null = null;
    let ro: ResizeObserver | null = null;
    let rafId = 0;
    let attempts = 0;
    let cancelled = false;

    const ensureView = (animate = false) => {
      if (cancelled || !map) return;
      if (el.clientWidth < MIN_CONTAINER || el.clientHeight < MIN_CONTAINER) {
        attempts += 1;
        if (attempts > 240) {
          setMapError('地图画布高度为 0，请刷新页面或切换到「示意图」');
          return;
        }
        setMapError(null);
        cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => ensureView(animate));
        return;
      }
      setMapError(null);
      map.invalidateSize({ animate: false });
      setupMapViewRef.current(map, extentRef.current, animate);
    };

    const mapBounds = L.latLngBounds([0, 0], [height, width]);

    map = L.map(el, {
      crs: L.CRS.Simple,
      minZoom: -2,
      maxZoom: 4,
      zoomSnap: 0.25,
      zoomControl: true,
      attributionControl: false,
      scrollWheelZoom: true,
      maxBoundsViscosity: 1,
      inertia: false,
    });
    mapRef.current = map;

    // 无描边满铺：与 .leaflet-container 同色，缩放/平移到边界外不出现框线接缝
    L.rectangle(mapBounds, {
      stroke: false,
      fillColor: '#0b1120',
      fillOpacity: 1,
    }).addTo(map);

    const edgeLayer = L.layerGroup().addTo(map);
    edgeLayerRef.current = edgeLayer;
    markersRef.current = [];

    for (const e of gisEdges) {
      const a = data.nodes.find((n) => n.id === e.source);
      const b = data.nodes.find((n) => n.id === e.target);
      if (!a || !b) continue;
      const isParent = e.kind === 'parent';
      L.polyline([toLeafletLatLng(a.x, a.y), toLeafletLatLng(b.x, b.y)], {
        color: isParent ? 'rgba(212,160,23,0.35)' : 'rgba(55,201,141,0.22)',
        weight: isParent ? 1 : 0.8,
        opacity: 0.5,
        dashArray: isParent ? '4 6' : undefined,
      }).addTo(edgeLayer);
    }

    for (const n of data.nodes) {
      const marker = L.circleMarker(toLeafletLatLng(n.x, n.y), {
        radius: baseGisMarkerRadius(n, coreIds),
        color: '#0f172a',
        weight: 1.2,
        fillColor: zoneColor(n.zone),
        fillOpacity: 0.92,
      }).addTo(map);

      const ch = n.chapters.length
        ? `第${n.chapters.slice(0, 4).join('、')}${n.chapters.length > 4 ? '…' : ''}回`
        : '';
      marker.bindPopup(
        `<div style="min-width:180px">
           <strong style="font-size:14px">${n.name}</strong><br/>
           <span style="color:#64748b;font-size:12px">${ZONE_LABELS[n.zone]}${ch ? ' · ' + ch : ''}</span>
           ${n.summary ? `<p style="margin:.4em 0;font-size:12px;line-height:1.5">${n.summary}</p>` : ''}
           <a href="/${bookSlug}/l/${encodeURIComponent(n.id)}" style="font-size:12px;color:#c2410c">地点详情 →</a>
         </div>`,
      );
      marker.bindTooltip(n.name, {
        permanent: n.id === '西门府' || n.id === '清河县',
        direction: 'bottom',
        offset: [0, 5],
        className: 'town-leaflet-label',
      });
      marker.on('click', (ev) => {
        L.DomEvent.stopPropagation(ev);
        if (activeRouteIdRef.current) setActiveRouteId(null);
        onSelectRef.current(n.id);
      });
      markersRef.current.push({ node: n, marker });
    }

    const onZoom = () => {
      if (!viewReadyRef.current) return;
      const min = anchorZoomRef.current;
      if (map!.getZoom() < min) map!.setZoom(min, { animate: false });
      applyVisuals(map!, extentRef.current, selectedIdRef.current);
    };

    map.on('zoom', onZoom);
    map.on('click', () => onSelectRef.current(null));

    const onLayout = () => ensureView(false);
    ro = new ResizeObserver(onLayout);
    ro.observe(el);
    window.addEventListener('graph-chrome-sync', onLayout);
    window.addEventListener('resize', onLayout);

    requestAnimationFrame(() => ensureView(false));
    const t = window.setTimeout(() => ensureView(false), 120);

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      window.clearTimeout(t);
      ro?.disconnect();
      window.removeEventListener('graph-chrome-sync', onLayout);
      window.removeEventListener('resize', onLayout);
      map?.off('zoom', onZoom);
      map?.remove();
      mapRef.current = null;
      edgeLayerRef.current = null;
      markersRef.current = [];
    };
  }, [applyVisuals, bookSlug, coreIds, data.nodes, gisEdges, height, width]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!extentReadyRef.current) {
      extentReadyRef.current = true;
      return;
    }
    setupMapViewRef.current(map, extent, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 仅切换视图时 refit
  }, [extent]);

  useEffect(() => {
    const map = mapRef.current;
    if (map && viewReadyRef.current) applyVisuals(map, extentRef.current, selectedId);
  }, [applyVisuals, selectedId]);

  // 事件路线：高亮选中路线的有序停靠点，淡化底图
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;

    routeLayerRef.current?.remove();
    routeLayerRef.current = null;

    const route = activeRouteId ? (data.routes ?? []).find((r) => r.id === activeRouteId) : null;

    if (!route) {
      edgeLayerRef.current?.eachLayer((l) =>
        (l as L.Polyline).setStyle?.({ opacity: extentRef.current === 'full' ? 0 : 0.5 }),
      );
      applyVisuals(map, extentRef.current, selectedIdRef.current);
      setupMapViewRef.current(map, extentRef.current, true);
      return;
    }

    edgeLayerRef.current?.eachLayer((l) => (l as L.Polyline).setStyle?.({ opacity: 0 }));
    for (const { marker } of markersRef.current) {
      marker.setStyle({ fillOpacity: 0.12, opacity: 0.3 });
      marker.getTooltip()?.closeTooltip?.();
    }

    const layer = L.layerGroup().addTo(map);
    routeLayerRef.current = layer;
    const latlngs = route.stops.map((s) => toLeafletLatLng(s.x, s.y));
    L.polyline(latlngs, { color: '#fcd34d', weight: 7, opacity: 0.16, lineCap: 'round' }).addTo(layer);
    L.polyline(latlngs, {
      color: '#fcd34d',
      weight: 2.5,
      opacity: 0.95,
      dashArray: '7 7',
      lineCap: 'round',
    }).addTo(layer);
    route.stops.forEach((s, i) => {
      const isLast = i === route.stops.length - 1;
      const m = L.marker(toLeafletLatLng(s.x, s.y), {
        icon: L.divIcon({
          className: '',
          html: `<div class="town-route-stop${isLast ? ' is-end' : ''}">${i + 1}</div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        }),
        zIndexOffset: 1000,
      }).addTo(layer);
      m.bindTooltip(`${i + 1}. ${s.name}`, {
        permanent: true,
        direction: 'top',
        offset: [0, -12],
        className: 'town-leaflet-label town-route-label',
      });
    });

    const rb = L.latLngBounds(latlngs);
    map.setMaxBounds(rb.pad(0.6));
    map.setMinZoom(-2);
    map.fitBounds(rb.pad(0.18), { animate: true, duration: 0.4, padding: FIT_PADDING });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- 仅路线切换/就绪时重绘
  }, [activeRouteId, data.routes, applyVisuals, ready]);

  if (data.nodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        暂无 GIS 坐标
      </div>
    );
  }

  return (
    <div className="absolute inset-0">
      <div ref={elRef} className="h-full w-full" />

      {mapError && (
        <div className="absolute inset-0 z-[700] flex items-center justify-center p-4">
          <p className="max-w-md rounded-xl border border-amber-500/30 bg-slate-900/92 px-4 py-3 text-center text-sm text-amber-100">
            {mapError}
          </p>
        </div>
      )}

      <div className="absolute right-3 top-14 z-[800] flex flex-col gap-1">
        {(
          [
            { key: 'core' as const, label: '清河详图' },
            { key: 'full' as const, label: '政商全图' },
          ] as const
        ).map((b) => (
          <button
            key={b.key}
            type="button"
            onClick={() => {
              if (activeRouteId) setActiveRouteId(null);
              setExtent(b.key);
            }}
            className="rounded-md border px-2.5 py-1 text-xs backdrop-blur-sm transition-colors"
            style={{
              borderColor: extent === b.key ? 'rgba(212,160,23,0.45)' : 'rgba(255,255,255,0.1)',
              backgroundColor: extent === b.key ? 'rgba(212,160,23,0.2)' : 'rgba(15,23,42,0.88)',
              color: extent === b.key ? '#fcd34d' : '#94a3b8',
            }}
          >
            {b.label}
          </button>
        ))}
      </div>

      {routes.length > 0 && (
        <div className="absolute left-3 top-16 z-[800] flex max-h-[calc(100%-9rem)] w-56 flex-col overflow-hidden rounded-lg border border-white/10 bg-slate-900/95">
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
                    onClick={() => {
                      setActiveRouteId(on ? null : r.id);
                      if (!on) onSelect(null);
                    }}
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
        <div className="pointer-events-none absolute left-1/2 top-14 z-[800] max-w-[calc(100%-1.5rem)] -translate-x-1/2 rounded-md bg-slate-900/95 px-3 py-1.5 text-center text-xs text-amber-100/90">
          {activeRoute.stops.map((s) => s.name).join(' → ')}
        </div>
      )}

      <div className="pointer-events-none absolute bottom-4 left-3 z-[500] flex flex-wrap gap-x-3 gap-y-1 rounded-md bg-slate-900/85 px-2.5 py-2 text-xs text-slate-400">
        {(Object.keys(ZONE_COLORS) as (keyof typeof ZONE_COLORS)[]).map((z) => (
          <span key={z} className="flex items-center gap-1.5">
            <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: ZONE_COLORS[z] }} />
            {ZONE_LABELS[z]}
          </span>
        ))}
      </div>
      <div className="pointer-events-none absolute bottom-4 left-1/2 z-[500] max-w-lg -translate-x-1/2 rounded-md bg-slate-900/85 px-3 py-1.5 text-center text-xs text-slate-500">
        {extent === 'core'
          ? '清河详图：滚轮只能放大 · 虚线隶属 · 实线近邻'
          : '政商全图：枢纽+远端标注 · 府内细点已收起 · 点「清河详图」回城'}
      </div>
    </div>
  );
}
