import { useMemo, useRef } from 'react';
import { ZONE_LABELS, ZONE_ORDER, type GardenMapNode, type GardenZone } from '../lib/gardenMap';

interface Props {
  nodes: GardenMapNode[];
  bookSlug: string;
  accent: string;
  accentSoft: string;
  onSelect: (id: string) => void;
  selectedId: string | null;
}

export default function GardenZoneCatalog({
  nodes,
  bookSlug,
  accent,
  accentSoft,
  onSelect,
  selectedId,
}: Props) {
  const rootRef = useRef<HTMLDivElement>(null);

  const byZone = useMemo(() => {
    const map = new Map<GardenZone, GardenMapNode[]>();
    for (const z of ZONE_ORDER) map.set(z, []);
    for (const n of nodes) {
      const list = map.get(n.zone) ?? [];
      list.push(n);
      map.set(n.zone, list);
    }
    for (const [z, list] of map) {
      list.sort((a, b) => {
        const ta = a.tourOrder ?? 999;
        const tb = b.tourOrder ?? 999;
        if (ta !== tb) return ta - tb;
        return a.name.localeCompare(b.name, 'zh-CN');
      });
    }
    return ZONE_ORDER.map((z) => ({ zone: z, items: map.get(z) ?? [] })).filter(
      (g) => g.items.length > 0,
    );
  }, [nodes]);

  const setAll = (open: boolean) => {
    rootRef.current?.querySelectorAll('details.garden-catalog-group').forEach((d) => {
      (d as HTMLDetailsElement).open = open;
    });
  };

  return (
    <div
      ref={rootRef}
      className="garden-catalog pointer-events-auto absolute left-3 top-16 z-10 flex max-h-[calc(100vh-5rem)] w-80 flex-col overflow-hidden rounded-xl border border-white/10 bg-slate-900/92 shadow-xl backdrop-blur-md"
    >
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-white/10 px-4 py-3">
        <span className="text-sm font-semibold text-slate-100">建筑名录</span>
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={() => setAll(true)}
            className="rounded-full border border-white/10 px-2.5 py-1 text-xs font-medium text-slate-300 hover:border-white/25 hover:text-white"
          >
            展开
          </button>
          <button
            type="button"
            onClick={() => setAll(false)}
            className="rounded-full border border-white/10 px-2.5 py-1 text-xs font-medium text-slate-300 hover:border-white/25 hover:text-white"
          >
            折叠
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2.5 py-2.5">
        {byZone.map(({ zone, items }) => (
          <details key={zone} className="garden-catalog-group mb-2 last:mb-0" open>
            <summary className="garden-catalog-summary cursor-pointer list-none rounded-md px-2.5 py-2 text-base font-bold text-slate-100 hover:bg-white/5">
              <span style={{ color: accentSoft }}>{ZONE_LABELS[zone]}</span>
              <span className="ml-2 text-sm font-medium text-slate-400">{items.length}</span>
            </summary>
            <ul className="mt-1.5 space-y-1.5 pb-1 pl-1">
              {items.map((n) => {
                const active = n.id === selectedId;
                return (
                  <li key={n.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(n.id)}
                      className="w-full rounded-md border px-3 py-2.5 text-left text-sm transition-colors hover:border-white/20 hover:bg-white/5"
                      style={{
                        borderColor: active ? `${accent}66` : 'rgba(255,255,255,0.08)',
                        backgroundColor: active ? `${accent}18` : 'transparent',
                        color: active ? accentSoft : '#e2e8f0',
                      }}
                    >
                      <div className="text-base font-semibold">{n.name}</div>
                      {n.plaque && (
                        <div className="mt-1 text-xs text-slate-400">匾 · {n.plaque}</div>
                      )}
                      {n.tourOrder != null && (
                        <div className="mt-1 text-xs font-medium text-amber-400/90">
                          游线第 {n.tourOrder} 站
                        </div>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </details>
        ))}
      </div>
      <div className="shrink-0 border-t border-white/10 px-4 py-3">
        <a
          href={`/${bookSlug}/places`}
          className="text-sm font-medium hover:underline"
          style={{ color: accent }}
        >
          全部建筑 →
        </a>
      </div>
    </div>
  );
}
