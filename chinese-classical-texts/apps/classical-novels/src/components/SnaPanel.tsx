import type { SnaData } from '../lib/sna';
import { proximityLabel, rankLabel } from '../lib/sna';

interface Props {
  data: SnaData;
  graphHref: string;
}

export default function SnaPanel({ data, graphHref }: Props) {
  const top = data.metrics.slice(0, 12);

  return (
    <div className="sna-panel space-y-8">
      <div className="grid gap-3 sm:grid-cols-3">
        {data.hubs.slice(0, 3).map((id, i) => (
          <div
            key={id}
            className="rounded-xl border px-4 py-3"
            style={{ borderColor: 'var(--line)', background: 'var(--surface)' }}
          >
            <div className="text-xs" style={{ color: 'var(--ink-soft)' }}>
              介数 Top {i + 1}
            </div>
            <div className="brand mt-1 text-xl" style={{ color: 'var(--primary)' }}>
              {id}
            </div>
          </div>
        ))}
      </div>

      <p className="text-sm leading-relaxed" style={{ color: 'var(--ink-soft)' }}>
        基于西门府社会网无向图近似计算度中心性与介数中心性（Brandes）。
        <strong style={{ color: 'var(--ink)' }}> 应伯爵、翟管家</strong>
        等帮闲/中介节点常居前列——信息与白银流动的掮客。
        <a href={graphHref} className="ml-1 hover:underline" style={{ color: 'var(--accent)' }}>
          打开关系图谱 →
        </a>
      </p>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr style={{ borderBottom: '1.5px solid var(--line)', color: 'var(--ink-soft)' }}>
              <th className="px-3 py-2 text-left font-normal">#</th>
              <th className="px-3 py-2 text-left font-normal">人物</th>
              <th className="px-3 py-2 text-left font-normal">派系</th>
              <th className="px-3 py-2 text-left font-normal">西门府距离</th>
              <th className="px-3 py-2 text-right font-normal">度</th>
              <th className="px-3 py-2 text-right font-normal">介数</th>
              <th className="px-3 py-2 text-left font-normal">等级</th>
            </tr>
          </thead>
          <tbody>
            {top.map((m, i) => (
              <tr key={m.id} style={{ borderBottom: '1px solid var(--line)' }}>
                <td className="px-3 py-2.5" style={{ color: 'var(--ink-soft)' }}>
                  {i + 1}
                </td>
                <td className="px-3 py-2.5 font-medium" style={{ color: 'var(--ink)' }}>
                  {m.id}
                </td>
                <td className="px-3 py-2.5" style={{ color: 'var(--ink-soft)' }}>
                  {m.faction ?? '—'}
                </td>
                <td className="px-3 py-2.5" style={{ color: 'var(--ink-soft)' }}>
                  {proximityLabel(m.ximen_proximity)}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">{m.degree}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">{m.betweenness.toFixed(4)}</td>
                <td className="px-3 py-2.5">
                  <span className="chip text-xs">{rankLabel(i)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
