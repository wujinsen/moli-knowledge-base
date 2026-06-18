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

export default function TownLeafletMap({ data, gis, bookSlug, selectedId, onSelect }: Props) {
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
        if (showLabel) tip.openTooltip();
        else tip.closeTooltip();
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

      applyVisuals(map, mode, selectedIdRef.current);
    },
    [applyVisuals, coreNodes, data.nodes],
  );
  const setupMapViewRef = useRef(setupMapView);
  setupMapViewRef.current = setupMapView;
  const extentReadyRef = useRef(false);

  useEffect(() => {
    const el = elRef.current;
    if (!el || data.nodes.length === 0) return;

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
    });
    mapRef.current = map;

    L.rectangle(mapBounds, {
      color: 'rgba(100,116,139,0.12)',
      weight: 1,
      fillColor: '#0b1120',
      fillOpacity: 0.95,
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
        onSelectRef.current(n.id);
      });
      markersRef.current.push({ node: n, marker });
    }

    const onZoom = () => {
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
    if (map) applyVisuals(map, extentRef.current, selectedId);
  }, [applyVisuals, selectedId]);

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

      <div className="absolute right-3 top-14 z-[600] flex flex-col gap-1">
        {(
          [
            { key: 'core' as const, label: '清河详图' },
            { key: 'full' as const, label: '政商全图' },
          ] as const
        ).map((b) => (
          <button
            key={b.key}
            type="button"
            onClick={() => setExtent(b.key)}
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
