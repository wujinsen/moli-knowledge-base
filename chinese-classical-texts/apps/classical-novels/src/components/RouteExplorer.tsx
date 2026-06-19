import { useEffect, useState } from 'react';
import RouteMap from './RouteMap';
import RouteLeafletMap from './RouteLeafletMap';
import type { RouteData } from '../lib/route';

interface Props {
  data: RouteData;
  bookSlug: string;
}

type Mode = 'schematic' | 'geo';

const graphHeight = 'calc(100dvh - var(--graph-chrome, 10.5rem))';

export default function RouteExplorer({ data, bookSlug }: Props) {
  const [mode, setMode] = useState<Mode>('schematic');

  useEffect(() => {
    const m = new URL(window.location.href).searchParams.get('map');
    if (m === 'geo' || m === 'schematic') setMode(m);
  }, []);

  const choose = (m: Mode) => {
    setMode(m);
    const url = new URL(window.location.href);
    if (m === 'geo') url.searchParams.set('map', 'geo');
    else url.searchParams.delete('map');
    window.history.replaceState({}, '', url.toString());
  };

  return (
    <div
      className="graph-explorer route-explorer relative overflow-hidden"
      style={{ height: graphHeight, minHeight: graphHeight }}
    >
      <div className="absolute left-1/2 top-3 z-[600] flex -translate-x-1/2 flex-col items-center">
        <div className="inline-flex gap-0.5 rounded-lg border border-white/10 bg-slate-900/85 p-0.5 backdrop-blur-sm">
          <button
            type="button"
            onClick={() => choose('schematic')}
            className="whitespace-nowrap rounded-md px-2.5 py-1 text-sm transition"
            style={{
              backgroundColor: mode === 'schematic' ? 'rgba(224,169,58,0.18)' : 'transparent',
              color: mode === 'schematic' ? '#f6df9a' : '#94a3b8',
              fontWeight: mode === 'schematic' ? 600 : 400,
            }}
          >
            章回路线
          </button>
          <button
            type="button"
            onClick={() => choose('geo')}
            className="whitespace-nowrap rounded-md px-2.5 py-1 text-sm transition"
            style={{
              backgroundColor: mode === 'geo' ? 'rgba(224,169,58,0.18)' : 'transparent',
              color: mode === 'geo' ? '#f6df9a' : '#94a3b8',
              fontWeight: mode === 'geo' ? 600 : 400,
            }}
          >
            真实地理
          </button>
        </div>
        <p className="pointer-events-none mt-1.5 max-w-[min(20rem,calc(100vw-2rem))] text-center text-xs leading-snug text-slate-500">
          {mode === 'schematic'
            ? '按书内章回排布，神话并置、火焰山北折，≠ 地球仪'
            : '丝路比附：瓦片底图 + 今地 + 经纬度'}
        </p>
      </div>

      {mode === 'schematic' ? (
        <RouteMap data={data} bookSlug={bookSlug} />
      ) : (
        <RouteLeafletMap data={data} bookSlug={bookSlug} />
      )}
    </div>
  );
}
