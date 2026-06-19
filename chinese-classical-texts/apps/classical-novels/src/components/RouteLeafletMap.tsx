import { useEffect, useMemo, useRef } from 'react';
import 'leaflet/dist/leaflet.css';
import L from '../lib/leafletClient';
import { realmColor, type RouteData } from '../lib/route';
import { formatGeoCoord, geoAnchor, geoMapLabel } from '../lib/routeGeo';

interface Props {
  data: RouteData;
  bookSlug: string;
}

/** 真实瓦片底图（CARTO dark）上叠加凡间取经路线。坐标多为丝路比附/象征，非测绘定稿。 */
export default function RouteLeafletMap({ data, bookSlug }: Props) {
  const elRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  const realNodes = useMemo(
    () => data.nodes.filter((n) => n.layer === 'real' && n.geo),
    [data.nodes],
  );
  const path = useMemo(
    () => [...realNodes].filter((n) => n.order != null).sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    [realNodes],
  );

  useEffect(() => {
    if (!elRef.current || realNodes.length === 0) return;

    const map = L.map(elRef.current, { zoomControl: true, attributionControl: true, scrollWheelZoom: true });
    mapRef.current = map;

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 10,
      minZoom: 2,
    }).addTo(map);

    const latlngs = path.filter((n) => n.geo).map((n) => [n.geo!.lat, n.geo!.lng] as [number, number]);
    if (latlngs.length > 1) {
      L.polyline(latlngs, {
        color: '#e0a93a',
        weight: 2.5,
        opacity: 0.85,
        dashArray: '6 6',
      }).addTo(map);
    }

    for (const n of realNodes) {
      if (!n.geo) continue;
      const color = realmColor(n.realm);
      const marker = L.circleMarker([n.geo.lat, n.geo.lng], {
        radius: n.order != null ? 7 : 5,
        color: '#0f172a',
        weight: 1.5,
        fillColor: color,
        fillOpacity: 0.95,
      }).addTo(map);

      const tribs = n.tribulations
        .slice(0, 6)
        .map((t) => `<li>第${t.no}难 ${t.title}</li>`)
        .join('');
      const orderTxt = n.order != null ? `第 ${n.order} 站 · ` : '';
      const chTxt = n.chapters.length ? `第${n.chapters.join('、')}回` : '';
      const anchor = geoAnchor(n.id);
      const coordTxt = n.geo ? formatGeoCoord(n.geo) : '';
      marker.bindPopup(
        `<div style="min-width:180px">
           <strong style="font-size:14px">${n.name}</strong>
           ${anchor ? `<br/><span style="color:#c2410c;font-size:12px">比附今地：${anchor}</span>` : ''}
           ${coordTxt ? `<br/><span style="color:#64748b;font-size:11px;font-family:monospace">${coordTxt}</span>` : ''}
           <br/><span style="color:#64748b;font-size:12px">${orderTxt}${n.realm} ${chTxt}</span>
           ${n.summary ? `<p style="margin:.4em 0;font-size:12px;line-height:1.5">${n.summary}</p>` : ''}
           ${tribs ? `<ul style="margin:.2em 0 .4em 1em;padding:0;font-size:12px">${tribs}</ul>` : ''}
           <a href="/${bookSlug}/l/${encodeURIComponent(n.id)}" style="font-size:12px;color:#c2410c">地点详情 →</a>
         </div>`,
      );
      marker.bindTooltip(geoMapLabel(n.id, n.name, n.order), {
        permanent: n.order != null,
        direction: 'bottom',
        offset: [0, 6],
        className: 'route-leaflet-label',
      });
    }

    const bounds = L.latLngBounds(realNodes.filter((n) => n.geo).map((n) => [n.geo!.lat, n.geo!.lng]));
    map.fitBounds(bounds, { padding: [48, 48] });
    const t = window.setTimeout(() => map.invalidateSize(), 60);

    const ro = new ResizeObserver(() => map.invalidateSize());
    ro.observe(elRef.current);

    return () => {
      window.clearTimeout(t);
      ro.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, [realNodes, path, bookSlug]);

  if (realNodes.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-slate-400">
        暂无带经纬度的凡间站点
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <div ref={elRef} className="absolute inset-0 h-full w-full" />
      <div className="pointer-events-none absolute bottom-4 left-1/2 z-[500] -translate-x-1/2 rounded-md bg-slate-900/80 px-3 py-1.5 text-center text-xs text-slate-400">
        真实瓦片底图 · 标注为「小说名→比附今地」+ 经纬度 · 坐标多为近似/象征
      </div>
    </div>
  );
}
