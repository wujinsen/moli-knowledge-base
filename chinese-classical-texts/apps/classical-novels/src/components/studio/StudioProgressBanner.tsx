import { useEffect, useState } from 'react';

export function useElapsedSeconds(active: boolean): number {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!active) {
      setElapsed(0);
      return;
    }
    const started = Date.now();
    const id = window.setInterval(() => {
      setElapsed(Math.floor((Date.now() - started) / 1000));
    }, 400);
    return () => window.clearInterval(id);
  }, [active]);

  return elapsed;
}

export type ProgressMetrics = {
  step?: number;
  total?: number;
  lineIndex?: number;
  lineTotal?: number;
};

type Props = {
  title: string;
  detail?: string;
  elapsedSeconds: number;
  progress?: ProgressMetrics | null;
};

function resolvePercent(progress?: ProgressMetrics | null): number | null {
  if (!progress) return null;
  if (progress.lineIndex && progress.lineTotal && progress.lineTotal > 0) {
    return Math.min(100, Math.round((progress.lineIndex / progress.lineTotal) * 100));
  }
  if (progress.step && progress.total && progress.total > 0) {
    return Math.min(100, Math.round((progress.step / progress.total) * 100));
  }
  return null;
}

/** 长耗时任务进度：支持 SSE 分步百分比或不确定进度条 */
export default function StudioProgressBanner({ title, detail, elapsedSeconds, progress }: Props) {
  const percent = resolvePercent(progress);

  return (
    <div className="studio-progress-banner" role="status" aria-live="polite">
      <div className="studio-progress-head">
        <span className="studio-progress-title">{title}</span>
        <span className="studio-progress-elapsed">
          {percent != null ? `${percent}% · ` : ''}已等待 {elapsedSeconds}s
        </span>
      </div>
      {detail ? <p className="studio-progress-detail">{detail}</p> : null}
      <div className="studio-progress-bar-track" aria-hidden="true">
        {percent != null ? (
          <div className="studio-progress-bar-determinate" style={{ width: `${percent}%` }} />
        ) : (
          <div className="studio-progress-bar-indeterminate" />
        )}
      </div>
    </div>
  );
}
