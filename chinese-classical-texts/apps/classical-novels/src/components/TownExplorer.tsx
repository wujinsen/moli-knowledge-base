import { useCallback, useMemo, useState } from 'react';
import TownLeafletMap from './TownLeafletMap';
import TownMap from './TownMap';
import { buildTownGisEdges, type TownGisMeta, type TownMapData } from '../lib/townMap';

interface Props {
  data: TownMapData;
  gis: TownGisMeta;
  bookSlug: string;
  initialView?: 'gis' | 'schematic';
}

type ViewMode = 'gis' | 'schematic';

export default function TownExplorer({ data, gis, bookSlug, initialView = 'gis' }: Props) {
  const [view, setView] = useState<ViewMode>(initialView);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedNode = useMemo(
    () => (selectedId ? data.nodes.find((n) => n.id === selectedId) ?? null : null),
    [data.nodes, selectedId],
  );

  const gisEdges = useMemo(() => buildTownGisEdges(data.nodes), [data.nodes]);

  const onSelect = useCallback((id: string | null) => setSelectedId(id), []);

  return (
    <div className="graph-explorer town-explorer relative overflow-hidden">
      <div className="absolute left-0 right-0 top-3 z-[600] flex flex-wrap items-center justify-center gap-2 px-3">
        <div className="flex rounded-lg border border-white/10 bg-slate-900/85 p-1 backdrop-blur-sm">
          <button
            type="button"
            onClick={() => setView('gis')}
            className="rounded-md px-3 py-1 text-xs transition-colors"
            style={{
              backgroundColor: view === 'gis' ? 'rgba(212,160,23,0.25)' : 'transparent',
              color: view === 'gis' ? '#fcd34d' : '#94a3b8',
            }}
          >
            GIS 地图
          </button>
          <button
            type="button"
            onClick={() => setView('schematic')}
            className="rounded-md px-3 py-1 text-xs transition-colors"
            style={{
              backgroundColor: view === 'schematic' ? 'rgba(212,160,23,0.25)' : 'transparent',
              color: view === 'schematic' ? '#fcd34d' : '#94a3b8',
            }}
          >
            示意图
          </button>
        </div>
        <span className="text-xs text-slate-500">
          {data.nodes.length} 处 · GIS {gisEdges.length} 条邻接（示意 {data.edges.length} 条）
        </span>
      </div>

      {view === 'gis' ? (
        <>
          <TownLeafletMap
            data={data}
            gis={gis}
            bookSlug={bookSlug}
            selectedId={selectedId}
            onSelect={onSelect}
          />
          {selectedNode && (
            <TownDetailPanel node={selectedNode} bookSlug={bookSlug} onClose={() => setSelectedId(null)} />
          )}
        </>
      ) : (
        <TownMap data={data} bookSlug={bookSlug} />
      )}
    </div>
  );
}

function TownDetailPanel({
  node,
  bookSlug,
  onClose,
}: {
  node: TownMapData['nodes'][0];
  bookSlug: string;
  onClose: () => void;
}) {
  return (
    <aside className="absolute right-3 top-28 z-[500] max-h-[calc(100vh-8rem)] w-64 overflow-y-auto rounded-xl border border-amber-900/40 bg-slate-900/92 p-4 shadow-xl backdrop-blur-md">
      <button type="button" onClick={onClose} className="absolute right-2 top-2 text-slate-500 hover:text-white">
        ×
      </button>
      <div className="mb-1 text-lg font-semibold text-amber-200">{node.name}</div>
      <p className="mb-3 text-sm leading-snug text-slate-300">{node.summary}</p>
      <a
        href={`/${bookSlug}/l/${encodeURIComponent(node.id)}`}
        className="text-sm text-amber-400 hover:underline"
      >
        地点详情 →
      </a>
    </aside>
  );
}
