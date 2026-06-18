import { useEffect, useState } from 'react';
import RouteMap from './RouteMap';
import RouteLeafletMap from './RouteLeafletMap';
import type { RouteData } from '../lib/route';

interface Props {
  data: RouteData;
  bookSlug: string;
}

type Mode = 'schematic' | 'geo';

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
    <div className="relative h-full w-full">
      {/* 视图切换：示意图 / 真实地理 */}
      <div className="absolute left-1/2 top-3 z-[600] -translate-x-1/2">
        <div className="flex gap-1 rounded-lg border border-white/10 bg-slate-900/85 p-1 backdrop-blur-sm">
          <button
            type="button"
            onClick={() => choose('schematic')}
            className="rounded-md px-3 py-1 text-sm transition"
            style={{
              backgroundColor: mode === 'schematic' ? 'rgba(224,169,58,0.18)' : 'transparent',
              color: mode === 'schematic' ? '#f6df9a' : '#94a3b8',
              fontWeight: mode === 'schematic' ? 600 : 400,
            }}
          >
            示意图
          </button>
          <button
            type="button"
            onClick={() => choose('geo')}
            className="rounded-md px-3 py-1 text-sm transition"
            style={{
              backgroundColor: mode === 'geo' ? 'rgba(224,169,58,0.18)' : 'transparent',
              color: mode === 'geo' ? '#f6df9a' : '#94a3b8',
              fontWeight: mode === 'geo' ? 600 : 400,
            }}
          >
            真实地理
          </button>
        </div>
      </div>

      {mode === 'schematic' ? (
        <RouteMap data={data} bookSlug={bookSlug} />
      ) : (
        <RouteLeafletMap data={data} bookSlug={bookSlug} />
      )}
    </div>
  );
}
