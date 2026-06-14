import { useCallback, useEffect, useMemo, useRef } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { SankeyData } from '../lib/transactions';
import { POOL_COLORS } from '../lib/transactions';

interface Props {
  sankey: SankeyData;
  totalLiang: number;
}

export default function SilverFlow({ sankey, totalLiang }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);

  const option = useMemo((): EChartsOption => {
    const nodeColors = sankey.nodes.map((n) => POOL_COLORS[n.name] ?? '#607a67');
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
        formatter: (p: any) => {
          if (p.dataType === 'edge') {
            const txs = p.data.txs as string[] | undefined;
            const txLine = txs?.length ? `<br/>${txs.length} 笔交易` : '';
            return `${p.data.source} → ${p.data.target}<br/><b>${p.data.value} 两</b>${txLine}`;
          }
          return `<b>${p.name}</b>`;
        },
      },
      series: [
        {
          type: 'sankey',
          layoutIterations: 32,
          nodeGap: 14,
          nodeWidth: 18,
          draggable: false,
          emphasis: { focus: 'adjacency' },
          lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.45 },
          label: {
            color: '#1f261f',
            fontFamily: '"Noto Serif SC", serif',
            fontSize: 12,
          },
          data: sankey.nodes.map((n, i) => ({
            name: n.name,
            itemStyle: { color: nodeColors[i] },
          })),
          links: sankey.links.map((l) => ({
            source: l.source,
            target: l.target,
            value: l.value,
            txs: l.txs,
          })),
        },
      ],
    };
  }, [sankey]);

  const render = useCallback(() => {
    if (!chartRef.current) return;
    if (!inst.current) inst.current = echarts.init(chartRef.current);
    inst.current.setOption(option, true);
  }, [option]);

  useEffect(() => {
    render();
    const ro = new ResizeObserver(() => inst.current?.resize());
    if (chartRef.current) ro.observe(chartRef.current);
    return () => {
      ro.disconnect();
      inst.current?.dispose();
      inst.current = null;
    };
  }, [render]);

  return (
    <div className="silver-flow">
      <p className="mb-3 text-sm" style={{ color: 'var(--ink-soft)' }}>
        已录入 <strong style={{ color: 'var(--accent)' }}>{totalLiang.toFixed(0)}+</strong> 两银量级流向（标准化口径，见换算说明）
      </p>
      <div
        ref={chartRef}
        className="w-full rounded-xl border"
        style={{
          height: 420,
          borderColor: 'var(--line)',
          background: 'color-mix(in srgb, var(--paper-2) 80%, white)',
        }}
      />
    </div>
  );
}
