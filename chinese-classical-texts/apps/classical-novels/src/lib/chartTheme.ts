/** ECharts 与全站 kb-dashboard 统一的图表配色 */

import { graphTheme } from './graphTheme';

export const KB_CHART = {
  tooltipBg: 'rgba(31, 38, 31, 0.92)',
  tooltipBorder: 'rgba(156, 132, 80, 0.4)',
  tooltipText: '#ecece1',
  axisLabel: '#5c6359',
  axisName: '#5c6359',
  axisLine: 'rgba(92, 99, 89, 0.35)',
  splitLine: 'rgba(92, 99, 89, 0.12)',
  legend: '#5c6359',
  ink: '#1f261f',
  sage: '#607a67',
  bronze: '#9c8450',
} as const;

export function kbChartTooltip() {
  return {
    backgroundColor: KB_CHART.tooltipBg,
    borderColor: KB_CHART.tooltipBorder,
    textStyle: { color: KB_CHART.tooltipText, fontSize: 13 },
  };
}

/** 膳食曲线：奢侈度用描金、平衡轴用松绿 */
export function dietChartPalette(bookSlug: string) {
  const t = graphTheme(bookSlug);
  return {
    luxury: t.accent,
    luxurySoft: t.accentSoft,
    luxuryArea: `${t.accent}22`,
    balance: KB_CHART.sage,
    milestone: t.accentSoft,
    milestoneDim: KB_CHART.axisLabel,
    phaseLine: KB_CHART.axisLine,
  };
}
