import { useCallback, useEffect, useMemo, useState } from 'react';
import { applyDreamTier, fetchDreamCatalog, fetchDreamPreview } from '../../lib/studio/client';
import type { BookSlug, DreamCatalog, DreamTierPreview } from '../../lib/studio/types';

type Props = {
  bookSlug: BookSlug;
  onOpenEntity?: (entityId: string) => void;
};

export default function DreamDashboard({ bookSlug, onOpenEntity }: Props) {
  const [catalog, setCatalog] = useState<DreamCatalog | null>(null);
  const [preview, setPreview] = useState<DreamTierPreview | null>(null);
  const [tierId, setTierId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyMsg, setApplyMsg] = useState<string | null>(null);

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

  const runPreview = useCallback(async (id: string) => {
    if (!id) return;
    setPreviewing(true);
    setError(null);
    setApplyMsg(null);
    try {
      const data = await fetchDreamPreview(bookSlug, id);
      setPreview(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPreviewing(false);
    }
  }, [bookSlug]);

  useEffect(() => {
    if (tierId && catalog?.supported !== false) {
      runPreview(tierId);
    }
  }, [tierId, catalog?.supported, runPreview]);

  const selectedTier = useMemo(
    () => catalog?.tiers.find((t) => t.id === tierId),
    [catalog, tierId],
  );

  const handleApply = async () => {
    if (!tierId || !preview) return;
    const ok = window.confirm(
      `确认执行 ${preview.label}？\n\n将修改多个人物 md，并依次运行：\n${preview.postApply.map((c) => `· ${c}`).join('\n')}`,
    );
    if (!ok) return;

    setApplying(true);
    setError(null);
    setApplyMsg(null);
    try {
      const data = await applyDreamTier(bookSlug, tierId);
      setPreview(data);
      setApplyMsg(`已应用 ${data.patchCount} 项变更 · postApply ${data.postApplyResults?.length ?? 0} 步`);
      await loadCatalog();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setApplying(false);
    }
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

  return (
    <div className="studio-dream">
      <div className="studio-lint-toolbar">
        <div>
          <h2 className="studio-batch-title">/dream tier 压平</h2>
          <p className="studio-batch-lead">
            hub 互链 / trust_guard 可核 rel · dry-run 预览后再应用 · 仅红楼梦
          </p>
        </div>
        <button type="button" className="studio-btn studio-btn-primary" disabled={loading} onClick={loadCatalog}>
          {loading ? '刷新中…' : '刷新目录'}
        </button>
      </div>

      {error && <div className="studio-banner studio-banner-error">{error}</div>}
      {applyMsg && <div className="studio-banner studio-banner-ok">{applyMsg}</div>}

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
              <span className="studio-lint-stat-num">{preview?.patchCount ?? '—'}</span>
              <span className="studio-lint-stat-label">预览变更</span>
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
                        {preview?.patchCount ?? '…'} · stuck {preview?.stuckCount ?? '…'}
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

                  {previewing && <div className="studio-banner">生成 dry-run 预览…</div>}

                  {preview && preview.candidateCount === 0 && (
                    <p className="studio-lint-empty">该梯队无待压平人物（可能已完成）✓</p>
                  )}

                  {preview && preview.patchCount > 0 && (
                    <>
                      <h4 className="studio-lint-subtitle">变更预览 ({preview.patchCount})</h4>
                      <ul className="studio-lint-entity-list">
                        {preview.changes.map((row) => (
                          <li key={row.summary}>
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
                        {preview.truncatedChanges ? (
                          <li className="studio-lint-more">… 另有 {preview.truncatedChanges} 条</li>
                        ) : null}
                      </ul>
                    </>
                  )}

                  {preview && preview.stuckCount > 0 && (
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
