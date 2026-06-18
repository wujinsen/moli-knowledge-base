import { useCallback, useEffect, useMemo, useRef } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { ChainIndex } from '../lib/chainIndex';
import {
  PHASE_COLORS,
  chainCumulativeCurve,
  chainScatterPoints,
  filterEventsByPhase,
  phaseChartRows,
  type ChainScatterPoint,
} from '../lib/chainCharts';

interface Props {
  index: ChainIndex;
  phaseKey: string | null;
  focusId: string | null;
  onPhaseChange: (key: string | null) => void;
  onEventFocus: (id: string) => void;
}

export default function ChainOverview({
  index,
  phaseKey,
  focusId,
  onPhaseChange,
  onEventFocus,
}: Props) {
  const phaseRef = useRef<HTMLDivElement>(null);
  const scatterRef = useRef<HTMLDivElement>(null);
  const curveRef = useRef<HTMLDivElement>(null);
  const phaseInst = useRef<echarts.ECharts | null>(null);
  const scatterInst = useRef<echarts.ECharts | null>(null);
  const curveInst = useRef<echarts.ECharts | null>(null);

  const phaseRows = useMemo(() => phaseChartRows(index), [index]);
  const visibleEvents = useMemo(
    () => filterEventsByPhase(index.events, phaseKey, index.phases),
    [index.events, index.phases, phaseKey],
  );
  const scatterPts = useMemo(() => chainScatterPoints(visibleEvents), [visibleEvents]);
  const curvePts = useMemo(() => chainCumulativeCurve(visibleEvents), [visibleEvents]);

  const phaseOption = useMemo((): EChartsOption => {
    return {
      backgroundColor: 'transparent',
      grid: { left: 40, right: 12, top: 40, bottom: 56 },
      tooltip: {
        trigger: 'axis',
        triggerOn: 'mousemove',
        axisPointer: { type: 'shadow' },
        confine: true,
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
        formatter: (params: { dataIndex?: number }[]) => {
          const row = phaseRows[params[0]?.dataIndex ?? 0];
          if (!row) return '';
          return `<b>${row.label}</b>（第${row.range[0]}–${row.range[1]}回）<br/>
            白银 ${row.financial} · 情节 ${row.plot}<br/>
            金额合计 <b>${row.liang} 两</b>`;
        },
      },
      legend: {
        data: ['白银', '情节'],
        top: 4,
        right: 8,
        itemWidth: 12,
        itemHeight: 12,
        textStyle: { color: '#5c6359', fontSize: 11 },
      },
      xAxis: {
        type: 'category',
        data: phaseRows.map((p) => p.label),
        axisLabel: {
          color: '#1f261f',
          fontSize: 11,
          interval: 0,
          rotate: 18,
          width: 56,
          overflow: 'truncate',
        },
        axisLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.35)' } },
      },
      yAxis: {
        type: 'value',
        name: '节点',
        minInterval: 1,
        nameTextStyle: { color: '#5c6359', fontSize: 11 },
        axisLabel: { color: '#5c6359', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.12)' } },
      },
      series: [
        {
          name: '白银',
          type: 'bar',
          stack: 'nodes',
          barMaxWidth: 36,
          data: phaseRows.map((p) => ({
            value: p.financial,
            itemStyle: { color: p.color },
          })),
        },
        {
          name: '情节',
          type: 'bar',
          stack: 'nodes',
          barMaxWidth: 36,
          data: phaseRows.map((p) => ({
            value: p.plot,
            itemStyle: { color: '#8a8578' },
          })),
        },
      ],
    };
  }, [phaseRows]);

  const scatterOption = useMemo((): EChartsOption => {
    const markAreas = index.phases.map((p) => [
      {
        xAxis: p.range[0],
        itemStyle: { color: `${PHASE_COLORS[p.key] ?? '#607a67'}14` },
      },
      { xAxis: p.range[1] + 0.9 },
    ]);

    const financial = scatterPts.filter((p) => p.subtype === 'financial');
    const plot = scatterPts.filter((p) => p.subtype === 'plot');

    return {
      backgroundColor: 'transparent',
      grid: { left: 52, right: 12, top: 28, bottom: 36 },
      legend: { show: false },
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        confine: true,
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
        formatter: (p: { data?: ChainScatterPoint & { value?: [number, number] } }) => {
          const d = p.data;
          if (!d?.id) return '';
          const amt = d.subtype === 'financial' ? `${d.amount} 两` : '情节节点';
          return `<b>${d.title}</b><br/>第 ${d.chapter} 回 · ${d.phaseLabel}<br/>${amt}`;
        },
      },
      xAxis: {
        type: 'value',
        min: 0,
        max: 100,
        name: '回',
        nameGap: 8,
        nameTextStyle: { color: '#5c6359', fontSize: 11 },
        axisLabel: { color: '#5c6359', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.08)' } },
      },
      yAxis: {
        type: 'value',
        name: '两',
        nameGap: 10,
        nameTextStyle: { color: '#5c6359', fontSize: 11 },
        axisLabel: { color: '#5c6359', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.12)' } },
      },
      series: [
        {
          name: '阶段',
          type: 'line',
          data: [] as number[],
          silent: true,
          markArea: {
            silent: true,
            data: markAreas,
          },
        },
        {
          name: '白银',
          type: 'scatter',
          symbolSize: (val: number[]) => Math.max(12, Math.min(36, Math.sqrt(val[1] ?? 1) * 2.2)),
          itemStyle: { color: '#9c8450' },
          data: financial.map((p) => ({
            ...p,
            value: [p.chapter, p.amount],
            itemStyle: {
              color: PHASE_COLORS[p.phase] ?? '#607a67',
              borderColor: focusId === p.id ? '#c45c26' : 'rgba(255,255,255,0.8)',
              borderWidth: focusId === p.id ? 3 : 1,
            },
          })),
        },
        {
          name: '情节',
          type: 'scatter',
          symbol: 'diamond',
          symbolSize: 14,
          itemStyle: { color: '#74332c' },
          data: plot.map((p) => ({
            ...p,
            value: [p.chapter, Math.max(p.amount, 12)],
            itemStyle: {
              color: PHASE_COLORS[p.phase] ?? '#74332c',
              borderColor: focusId === p.id ? '#c45c26' : 'rgba(255,255,255,0.8)',
              borderWidth: focusId === p.id ? 3 : 1,
            },
          })),
        },
      ],
    };
  }, [index.phases, scatterPts, focusId]);

  const curveOption = useMemo((): EChartsOption => {
    return {
      backgroundColor: 'transparent',
      grid: { left: 52, right: 16, top: 20, bottom: 44 },
      tooltip: {
        trigger: 'axis',
        triggerOn: 'mousemove',
        confine: true,
        axisPointer: { type: 'line', lineStyle: { color: 'rgba(156, 132, 80, 0.35)' } },
        backgroundColor: 'rgba(31, 38, 31, 0.92)',
        borderColor: 'rgba(156, 132, 80, 0.4)',
        textStyle: { color: '#ecece1', fontSize: 13 },
        formatter: (params: { dataIndex?: number }[]) => {
          const pt = curvePts[params[0]?.dataIndex ?? 0];
          if (!pt) return '';
          return `<b>${pt.title}</b><br/>第 ${pt.chapter} 回<br/>+${pt.delta} 两 · 累计 ${pt.cumulative} 两`;
        },
      },
      xAxis: {
        type: 'category',
        data: curvePts.map((_, i) => String(i + 1)),
        boundaryGap: false,
        axisLabel: {
          color: '#5c6359',
          fontSize: 10,
          interval: 0,
          formatter: (_: string, idx: number) => {
            const pt = curvePts[idx];
            if (!pt) return '';
            const prev = curvePts[idx - 1];
            if (prev && prev.chapter === pt.chapter) return '';
            return `${pt.chapter}`;
          },
        },
        axisLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.35)' } },
        axisTick: { alignWithLabel: true },
      },
      yAxis: {
        type: 'value',
        name: '累计两',
        nameGap: 12,
        nameTextStyle: { color: '#5c6359', fontSize: 11 },
        axisLabel: { color: '#5c6359', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(92, 99, 89, 0.12)' } },
      },
      series: [
        {
          type: 'line',
          smooth: 0.35,
          symbol: 'circle',
          symbolSize: (val: number, p: { dataIndex?: number }) =>
            focusId && curvePts[p.dataIndex ?? 0]?.id === focusId ? 9 : 5,
          lineStyle: { color: '#74332c', width: 2 },
          itemStyle: { color: '#9c8450' },
          areaStyle: { color: 'rgba(116, 51, 44, 0.08)' },
          data: curvePts.map((p) => p.cumulative),
        },
      ],
    };
  }, [curvePts, focusId]);

  const bindClicks = useCallback(() => {
    phaseInst.current?.off('click');
    phaseInst.current?.on('click', (p: { dataIndex?: number }) => {
      const row = phaseRows[p.dataIndex ?? 0];
      if (!row) return;
      onPhaseChange(phaseKey === row.key ? null : row.key);
    });

    const onScatter = (p: { data?: { id?: string } }) => {
      if (p.data?.id) onEventFocus(p.data.id);
    };
    scatterInst.current?.off('click');
    scatterInst.current?.on('click', onScatter);

    curveInst.current?.off('click');
    curveInst.current?.on('click', (p: { dataIndex?: number }) => {
      const pt = curvePts[p.dataIndex ?? 0];
      if (pt) onEventFocus(pt.id);
    });
  }, [curvePts, onEventFocus, onPhaseChange, phaseKey, phaseRows]);

  const renderCharts = useCallback(() => {
    try {
      if (phaseRef.current) {
        if (!phaseInst.current) phaseInst.current = echarts.init(phaseRef.current);
        phaseInst.current.setOption(phaseOption, true);
      }
      if (scatterRef.current) {
        if (!scatterInst.current) scatterInst.current = echarts.init(scatterRef.current);
        scatterInst.current.setOption(scatterOption, true);
      }
      if (curveRef.current) {
        if (!curveInst.current) curveInst.current = echarts.init(curveRef.current);
        curveInst.current.setOption(curveOption, true);
      }
      bindClicks();
      phaseInst.current?.dispatchAction({ type: 'hideTip' });
      scatterInst.current?.dispatchAction({ type: 'hideTip' });
      curveInst.current?.dispatchAction({ type: 'hideTip' });
    } catch (err) {
      console.error('[ChainOverview] chart render failed', err);
    }
  }, [bindClicks, curveOption, phaseOption, scatterOption]);

  useEffect(() => {
    renderCharts();
    const ro = new ResizeObserver(() => {
      phaseInst.current?.resize();
      scatterInst.current?.resize();
      curveInst.current?.resize();
    });
    for (const el of [phaseRef.current, scatterRef.current, curveRef.current]) {
      if (el) ro.observe(el);
    }
    return () => {
      ro.disconnect();
      phaseInst.current?.dispose();
      scatterInst.current?.dispose();
      curveInst.current?.dispose();
      phaseInst.current = null;
      scatterInst.current = null;
      curveInst.current = null;
    };
  }, [renderCharts]);

  return (
    <div className="chain-overview mb-8">
      <div className="mb-3 flex flex-wrap items-baseline gap-2">
        <h3 className="section-title text-sm">链式总览</h3>
        <span className="text-xs text-muted">
          四阶段节点分布 · 回目散点 · 节点金额累计（点击图表可筛选 / 定位）
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <p className="mb-1 text-xs text-muted">四阶段 · 节点数（点击柱筛选）</p>
          <div
            ref={phaseRef}
            className="w-full rounded-xl border"
            style={{
              height: 260,
              borderColor: 'var(--line)',
              background: 'color-mix(in srgb, var(--paper-2) 90%, white)',
            }}
          />
        </div>
        <div className="lg:col-span-3">
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-muted">全书回目 · 圆=白银 · 菱=情节</p>
            <div className="flex flex-wrap gap-1.5">
              {index.phases.map((p) => (
                <span
                  key={p.key}
                  className="chip text-[10px] leading-none"
                  style={{ borderColor: PHASE_COLORS[p.key], color: PHASE_COLORS[p.key] }}
                >
                  {p.label}
                </span>
              ))}
            </div>
          </div>
          <div
            ref={scatterRef}
            className="w-full rounded-xl border"
            style={{
              height: 260,
              borderColor: 'var(--line)',
              background: 'color-mix(in srgb, var(--paper-2) 90%, white)',
            }}
          />
        </div>
      </div>

      <p className="mb-1 mt-5 text-xs text-muted">
        节点金额累计（event.amount_liang · 横轴为链序，数字为回目）
      </p>
      <div
        ref={curveRef}
        className="w-full rounded-xl border"
        style={{
          height: 220,
          borderColor: 'var(--line)',
          background: 'color-mix(in srgb, var(--paper-2) 90%, white)',
        }}
      />
    </div>
  );
}
