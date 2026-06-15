import { useMemo, useRef } from 'react';
import {
  MANOR_ZONE_LABELS,
  MANOR_ZONE_ORDER,
  type ManorMapNode,
  type ManorZone,
} from '../lib/manorMap';

interface Props {
  nodes: ManorMapNode[];
  bookSlug: string;
  accent: string;
  accentSoft: string;
  onSelect: (id: string) => void;
  selectedId: string | null;
}

export default function ManorZoneCatalog({
  nodes,
  bookSlug,
  accent,
  accentSoft,
  onSelect,
  selectedId,
}: Props) {
  const rootRef = useRef<HTMLDivElement>(null);

  const byZone = useMemo(() => {
    const map = new Map<ManorZone, ManorMapNode[]>();
    for (const z of MANOR_ZONE_ORDER) map.set(z, []);
    for (const n of nodes) {
      const list = map.get(n.zone) ?? [];
      list.push(n);
      map.set(n.zone, list);
    }
    return MANOR_ZONE_ORDER.map((z) => ({ zone: z, items: map.get(z) ?? [] })).filter(
      (g) => g.items.length > 0,
    );
  }, [nodes]);

  const setAll = (open: boolean) => {
    rootRef.current?.querySelectorAll('details.manor-catalog-group').forEach((d) => {
      (d as HTMLDetailsElement).open = open;
    });
  };

  return (
    <div
      ref={rootRef}
      className="garden-catalog pointer-events-auto absolute left-3 top-16 z-10 flex max-h-[calc(100vh-5rem)] w-72 flex-col overflow-hidden rounded-xl border border-white/10 bg-slate-900/92 shadow-xl backdrop-blur-md"
    >
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-white/10 px-3 py-2.5">
        <span className="text-xs font-medium text-slate-300">两府名录</span>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => setAll(true)}
            className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-slate-400 hover:border-white/25 hover:text-white"
          >
            展开
          </button>
          <button
            type="button"
            onClick={() => setAll(false)}
            className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-slate-400 hover:border-white/25 hover:text-white"
          >
            折叠
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {byZone.map(({ zone, items }) => (
          <details key={zone} className="manor-catalog-group garden-catalog-group mb-2 last:mb-0" open>
            <summary className="garden-catalog-summary cursor-pointer list-none rounded-md px-2 py-1.5 text-sm font-semibold text-slate-200 hover:bg-white/5">
              <span style={{ color: accentSoft }}>{MANOR_ZONE_LABELS[zone]}</span>
              <span className="ml-1.5 text-xs font-normal text-slate-500">{items.length}</span>
            </summary>
            <ul className="mt-1 space-y-1 pb-1 pl-1">
              {items.map((n) => {
                const active = n.id === selectedId;
                return (
                  <li key={n.id}>
                    <button
                      type="button"
                      onClick={() => onSelect(n.id)}
                      className="w-full rounded-md border px-2.5 py-2 text-left text-xs transition-colors hover:border-white/20 hover:bg-white/5"
                      style={{
                        borderColor: active ? `${accent}66` : 'rgba(255,255,255,0.08)',
                        backgroundColor: active ? `${accent}18` : 'transparent',
                        color: active ? accentSoft : '#cbd5e1',
                      }}
                    >
                      <div className="font-medium">{n.name}</div>
                      {n.plaque && (
                        <div className="mt-0.5 text-[10px] text-slate-500">匾 · {n.plaque}</div>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </details>
        ))}
      </div>
      <div className="shrink-0 border-t border-white/10 px-3 py-2">
        <a href={`/${bookSlug}/places`} className="text-xs hover:underline" style={{ color: accent }}>
          全部建筑 →
        </a>
      </div>
    </div>
  );
}
