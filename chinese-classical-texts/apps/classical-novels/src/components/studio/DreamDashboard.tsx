import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchDreamCatalog,
  streamDreamApply,
  streamDreamPreview,
} from '../../lib/studio/client';
import type { BookSlug, DreamCatalog, DreamProgressEvent, DreamTierPreview } from '../../lib/studio/types';
import StudioProgressBanner, { type ProgressMetrics, useElapsedSeconds } from './StudioProgressBanner';

type Props = {
  bookSlug: BookSlug;
  onOpenEntity?: (entityId: string) => void;
};

type StreamState = {
  stage?: string;
  label?: string;
  lastLine?: string;
  patchCount?: number;
  progress: ProgressMetrics;
};

const STAGE_LABEL: Record<string, string> = {
  preview: '预览',
  patch: '写盘',
  postApply: 'postApply',
  refresh: '刷新预览',
};

function titleFromStream(stream: StreamState | null, applying: boolean): string {
  if (!stream) return applying ? '正在应用批次…' : '正在生成 dry-run 预览…';
  const stageName = STAGE_LABEL[stream.stage ?? ''] ?? stream.stage ?? '处理中';
  const { progress, patchCount, lastLine } = stream;
  if (stream.stage === 'preview' && progress.step && progress.total) {
    return `${stageName} ${progress.step}/${progress.total}${lastLine ? ` · ${lastLine}` : ''}`;
  }
  if (stream.stage === 'patch' && progress.lineIndex) {
    const totalHint = patchCount ? ` / 约 ${patchCount}` : progress.lineTotal ? ` / ${progress.lineTotal}` : '';
    return `${stageName} · 第 ${progress.lineIndex} 条${totalHint}`;
  }
  if (stream.stage === 'postApply' && progress.step && progress.total) {
    return `${stageName} ${progress.step}/${progress.total}`;
  }
  if (stream.label) return stream.label;
  return applying ? '正在应用批次…' : '正在生成 dry-run 预览…';
}

function detailFromStream(stream: StreamState | null): string | undefined {
  if (!stream?.lastLine) return undefined;
  return stream.lastLine;
}

export default function DreamDashboard({ bookSlug, onOpenEntity }: Props) {
  const [catalog, setCatalog] = useState<DreamCatalog | null>(null);
  const [preview, setPreview] = useState<DreamTierPreview | null>(null);
  const [tierId, setTierId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyMsg, setApplyMsg] = useState<string | null>(null);
  const [streamState, setStreamState] = useState<StreamState | null>(null);
  const [liveChanges, setLiveChanges] = useState<Array<{ summary: string; characterId?: string | null }>>([]);

  const streamAbortRef = useRef<(() => void) | null>(null);

  const busy = loading || previewing || applying;
  const elapsed = useElapsedSeconds(busy);

  const loadCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDreamCatalog(bookSlug);
      setCatalog(data);
      if (data.supported !== false) {
        const next = data.recommendedTierId ?? data.tiers.find((t) => t.candidateCount > 0)?.id ?? data.tiers[0]?.id ?? '';
        setTierId((prev) => prev || next);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [bookSlug]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  const handleProgress = useCallback((ev: DreamProgressEvent) => {
    setStreamState((prev) => {
      const base: StreamState = prev ?? { progress: {} };
      if (ev.event === 'stage') {
        return {
          stage: ev.stage,
          label: ev.label,
          lastLine: ev.text ?? ev.command,
          patchCount: base.patchCount,
          progress: {
            step: ev.step,
            total: ev.total,
            lineIndex: ev.stage === 'preview' ? ev.step : base.progress.lineIndex,
            lineTotal: ev.stage === 'preview' ? ev.total : base.progress.lineTotal,
          },
        };
      }
      if (ev.event === 'line') {
        return {
          ...base,
          stage: ev.stage ?? base.stage,
          lastLine: ev.text,
          progress: {
            ...base.progress,
            lineIndex: ev.index,
            lineTotal: ev.total ?? base.progress.lineTotal,
          },
        };
      }
      if (ev.event === 'milestone') {
        return {
          ...base,
          stage: ev.stage ?? base.stage,
          lastLine: ev.text,
          patchCount: ev.patchCount,
          progress: base.progress,
        };
      }
      if (ev.event === 'log' && ev.text) {
        return { ...base, lastLine: ev.text };
      }
      return base;
    });

    if (ev.event === 'line' && ev.text) {
      setLiveChanges((rows) => [...rows, { summary: ev.text!, characterId: ev.characterId }]);
    }
  }, []);

  const runPreview = useCallback((id: string) => {
    if (!id) return;
    streamAbortRef.current?.();
    setPreviewing(true);
    setError(null);
    setApplyMsg(null);
    setStreamState(null);
    setLiveChanges([]);

    streamAbortRef.current = streamDreamPreview(bookSlug, id, {
      onProgress: handleProgress,
      onDone: (data) => {
        setPreview(data);
        setPreviewing(false);
        setStreamState(null);
        setLiveChanges([]);
        streamAbortRef.current = null;
      },
      onError: (e) => {
        setError(e.message);
        setPreviewing(false);
        setStreamState(null);
        streamAbortRef.current = null;
      },
    });
  }, [bookSlug, handleProgress]);

  useEffect(() => {
    if (tierId && catalog?.supported !== false) {
      runPreview(tierId);
    }
  }, [tierId, catalog?.supported, runPreview]);

  useEffect(() => () => streamAbortRef.current?.(), []);

  const selectedTier = useMemo(
    () => catalog?.tiers.find((t) => t.id === tierId),
    [catalog, tierId],
  );

  const handleApply = () => {
    if (!tierId || !preview) return;
    const ok = window.confirm(
      `确认执行 ${preview.label}？\n\n将修改多个人物 md，并依次运行：\n${preview.postApply.map((c) => `· ${c}`).join('\n')}`,
    );
    if (!ok) return;

    streamAbortRef.current?.();
    setApplying(true);
    setError(null);
    setApplyMsg(null);
    setStreamState(null);
    setLiveChanges([]);

    streamAbortRef.current = streamDreamApply(bookSlug, tierId, {
      onProgress: handleProgress,
      onDone: async (data) => {
        setPreview(data);
        setApplyMsg(`已应用 ${data.patchCount} 项变更 · postApply ${data.postApplyResults?.length ?? 0} 步`);
        setApplying(false);
        setStreamState(null);
        streamAbortRef.current = null;
        await loadCatalog();
      },
      onError: (e) => {
        setError(e.message);
        setApplying(false);
        setStreamState(null);
        streamAbortRef.current = null;
      },
    });
  };

  if (catalog?.supported === false) {
    return (
      <div className="studio-batch-placeholder surface">
        <h2 className="studio-batch-title">/dream 睡眠巩固</h2>
        <p className="studio-batch-lead">{catalog.message}</p>
      </div>
    );
  }

  const scoreMax = catalog
    ? Math.max(...Object.values(catalog.scoreDistribution ?? {}).map(Number), 1)
    : 1;

  const progressTitle = loading
    ? '正在刷新梯队目录…'
    : titleFromStream(streamState, applying);

  const progressDetail = loading
    ? '统计 score 分布与各梯队候选数'
    : detailFromStream(streamState) ?? (
      applying
        ? `写盘 → postApply ${preview?.postApply.length ?? 0} 步 → 刷新预览`
        : previewing
          ? `扫描 ${selectedTier?.label ?? tierId} · 候选约 ${selectedTier?.candidateCount ?? '—'} 页`
          : undefined
    );

  const displayChanges = previewing && liveChanges.length > 0 ? liveChanges : preview?.changes ?? [];
  const displayPatchCount = previewing && liveChanges.length > 0 ? liveChanges.length : preview?.patchCount;

  return (
    <div className={`studio-dream${busy && !loading ? ' studio-dream-busy' : ''}`}>
      <div className="studio-lint-toolbar">
        <div>
          <h2 className="studio-batch-title">/dream tier 压平</h2>
          <p className="studio-batch-lead">
            hub 互链 / trust_guard 可核 rel · SSE 流式预览/应用 · 三书均支持
          </p>
        </div>
        <button type="button" className="studio-btn studio-btn-primary" disabled={loading} onClick={loadCatalog}>
          {loading ? '刷新中…' : '刷新目录'}
        </button>
      </div>

      {busy && progressTitle && (
        <StudioProgressBanner
          title={progressTitle}
          detail={progressDetail}
          elapsedSeconds={elapsed}
          progress={loading ? null : streamState?.progress}
        />
      )}

      {error && <div className="studio-banner studio-banner-error">{error}</div>}
      {applyMsg && !applying && <div className="studio-banner studio-banner-ok">{applyMsg}</div>}

      {catalog && (
        <>
          <div className="studio-lint-summary">
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{catalog.totalCharacters ?? '—'}</span>
              <span className="studio-lint-stat-label">人物页</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{catalog.recommendedTierId ?? '—'}</span>
              <span className="studio-lint-stat-label">推荐批次</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{displayPatchCount ?? '—'}</span>
              <span className="studio-lint-stat-label">{previewing ? '已扫描' : '预览变更'}</span>
            </div>
          </div>

          <div className="studio-lint-grid">
            <section className="studio-lint-panel">
              <h3 className="studio-lint-panel-title">梯队目录</h3>
              <ul className="studio-dream-tiers">
                {catalog.tiers.map((t) => (
                  <li key={t.id}>
                    <button
                      type="button"
                      className={
                        tierId === t.id ? 'studio-lint-sec-btn studio-lint-sec-btn-active' : 'studio-lint-sec-btn'
                      }
                      disabled={busy}
                      onClick={() => setTierId(t.id)}
                    >
                      <span>
                        {t.label}
                        <span className="studio-dream-tier-sub">
                          {t.thinLabel} → {t.goal}
                        </span>
                      </span>
                      <span className={t.candidateCount ? 'studio-lint-badge-warn' : 'studio-lint-badge-ok'}>
                        {t.candidateCount}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>

              {catalog.scoreDistribution && (
                <>
                  <h4 className="studio-lint-subtitle">当前 score 分布（节选）</h4>
                  <div className="studio-score-bars studio-score-bars-compact">
                    {Object.entries(catalog.scoreDistribution)
                      .sort(([a], [b]) => Number(a) - Number(b))
                      .slice(0, 12)
                      .map(([score, count]) => (
                        <div key={score} className="studio-score-row">
                          <span className="studio-score-label">{score}</span>
                          <div className="studio-score-bar-track">
                            <div
                              className="studio-score-bar-fill"
                              style={{ width: `${(count / scoreMax) * 100}%` }}
                            />
                          </div>
                          <span className="studio-score-count">{count}</span>
                        </div>
                      ))}
                  </div>
                </>
              )}
            </section>

            <section className="studio-lint-panel studio-lint-detail">
              {selectedTier && (
                <>
                  <div className="studio-dream-preview-head">
                    <div>
                      <h3 className="studio-lint-panel-title">
                        {selectedTier.label} · dry-run
                      </h3>
                      <p className="studio-lint-hint">
                        候选 {preview?.candidateCount ?? selectedTier.candidateCount} · 可改{' '}
                        {displayPatchCount ?? '…'} · stuck {preview?.stuckCount ?? '…'}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="studio-btn studio-btn-primary"
                      disabled={
                        previewing ||
                        applying ||
                        !preview ||
                        preview.candidateCount === 0 ||
                        preview.patchCount === 0
                      }
                      onClick={handleApply}
                    >
                      {applying ? '应用中…' : '应用批次'}
                    </button>
                  </div>

                  {preview && preview.candidateCount === 0 && !previewing && (
                    <p className="studio-lint-empty">该梯队无待压平人物（可能已完成）✓</p>
                  )}

                  {(displayPatchCount ?? 0) > 0 && (
                    <>
                      <h4 className="studio-lint-subtitle">
                        变更预览 ({displayPatchCount})
                        {previewing ? ' · 流式追加中' : ''}
                      </h4>
                      <ul className="studio-lint-entity-list studio-dream-live-list">
                        {(previewing ? displayChanges.slice(-80) : displayChanges).map((row, idx) => (
                          <li key={`${idx}-${row.summary}`}>
                            {row.characterId && onOpenEntity ? (
                              <button
                                type="button"
                                className="studio-lint-entity-link"
                                onClick={() => onOpenEntity(row.characterId!)}
                              >
                                {row.summary}
                              </button>
                            ) : (
                              <span>{row.summary}</span>
                            )}
                          </li>
                        ))}
                        {previewing && displayChanges.length > 80 ? (
                          <li className="studio-lint-more">… 上方仅显示最近 80 条</li>
                        ) : null}
                        {!previewing && preview?.truncatedChanges ? (
                          <li className="studio-lint-more">… 另有 {preview.truncatedChanges} 条</li>
                        ) : null}
                      </ul>
                    </>
                  )}

                  {preview && preview.stuckCount > 0 && !previewing && (
                    <>
                      <h4 className="studio-lint-subtitle">无法自动处理 ({preview.stuckCount})</h4>
                      <ul className="studio-lint-lines">
                        {preview.stuck.map((row) => (
                          <li key={row.id}>
                            {onOpenEntity ? (
                              <button
                                type="button"
                                className="studio-lint-entity-link"
                                onClick={() => onOpenEntity(row.id)}
                              >
                                {row.id}
                              </button>
                            ) : (
                              row.id
                            )}{' '}
                            score={row.score} rel={row.rel} plot={row.plot} 入链={row.inbound}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {preview?.postApply.length ? (
                    <p className="studio-lint-hint studio-dream-postapply">
                      应用后 postApply：{preview.postApply.join(' → ')}
                    </p>
                  ) : null}
                </>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
