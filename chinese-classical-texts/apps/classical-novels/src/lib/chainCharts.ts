import type { ChainEventRow, ChainIndex, ChainPhase } from './chainIndex';

export const PHASE_COLORS: Record<string, string> = {
  rise: '#607a67',
  climb: '#9c8450',
  peak: '#74332c',
  fall: '#4a5568',
};

export interface PhaseChartRow {
  key: string;
  label: string;
  range: [number, number];
  financial: number;
  plot: number;
  liang: number;
  color: string;
}

export function phaseChartRows(index: ChainIndex): PhaseChartRow[] {
  return index.phases.map((p) => {
    const evts = eventsInPhase(index.events, p);
    return {
      key: p.key,
      label: p.label,
      range: p.range,
      financial: evts.filter((e) => e.subtype === 'financial').length,
      plot: evts.filter((e) => e.subtype === 'plot').length,
      liang: Math.round(evts.reduce((s, e) => s + (e.amount_liang ?? 0), 0) * 10) / 10,
      color: PHASE_COLORS[p.key] ?? '#607a67',
    };
  });
}

export function eventsInPhase(events: ChainEventRow[], phase: ChainPhase): ChainEventRow[] {
  const [lo, hi] = phase.range;
  return events.filter((e) => e.chapter >= lo && e.chapter <= hi);
}

export function filterEventsByPhase(events: ChainEventRow[], phaseKey: string | null, phases: ChainPhase[]) {
  if (!phaseKey) return events;
  const ph = phases.find((p) => p.key === phaseKey);
  if (!ph) return events;
  return eventsInPhase(events, ph);
}

export interface ChainScatterPoint {
  id: string;
  title: string;
  chapter: number;
  amount: number;
  subtype: string;
  phase: string;
  phaseLabel: string;
}

export function chainScatterPoints(events: ChainEventRow[]): ChainScatterPoint[] {
  return events.map((e) => ({
    id: e.id,
    title: e.title,
    chapter: e.chapter,
    amount: e.amount_liang ?? (e.subtype === 'plot' ? 8 : 4),
    subtype: e.subtype,
    phase: e.phase,
    phaseLabel: e.phase_label,
  }));
}

export interface ChainCurvePoint {
  chapter: number;
  cumulative: number;
  delta: number;
  id: string;
  title: string;
}

export function chainCumulativeCurve(events: ChainEventRow[]): ChainCurvePoint[] {
  let cumulative = 0;
  return events.map((e) => {
    const delta = e.amount_liang ?? 0;
    cumulative += delta;
    return {
      chapter: e.chapter,
      cumulative: Math.round(cumulative * 10) / 10,
      delta,
      id: e.id,
      title: e.title,
    };
  });
}
