import { useCallback, useEffect, useState } from 'react';
import { fetchGuardReport } from '../../lib/studio/client';
import type { BookSlug, GuardIssueItem, GuardReport } from '../../lib/studio/types';

type Props = {
  bookSlug: BookSlug;
  onOpenEntity?: (entityId: string) => void;
};

function entityIdOf(item: GuardIssueItem): string | undefined {
  return item.characterId ?? item.entityId;
}

export default function GuardDashboard({ bookSlug, onOpenEntity }: Props) {
  const [report, setReport] = useState<GuardReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSection, setOpenSection] = useState<string>('plot');

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGuardReport(bookSlug);
      setReport(data);
      const first = data.sections.find((s) => s.count > 0);
      setOpenSection(first?.id ?? 'plot');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [bookSlug]);

  useEffect(() => {
    run();
  }, [run]);

  const generatedLabel = report
    ? new Date(report.generatedAt).toLocaleString('zh-CN', { hour12: false })
    : '';

  const active = report?.sections.find((s) => s.id === openSection);

  return (
    <div className="studio-guard">
      <div className="studio-lint-toolbar">
        <div>
          <h2 className="studio-batch-title">/guard Trust Guard</h2>
          <p className="studio-batch-lead">
            content 层回原文核对：first_appear · 关键情节 · relations · transactions（只报告）
          </p>
        </div>
        <button type="button" className="studio-btn studio-btn-primary" disabled={loading} onClick={run}>
          {loading ? '校验中…' : '重新校验'}
        </button>
      </div>

      {error && <div className="studio-banner studio-banner-error">{error}</div>}

      {loading && !report && <div className="studio-banner">全库校验中，首次可能需 1–2 分钟…</div>}

      {report && (
        <>
          <div className="studio-lint-summary">
            <div
              className={
                report.passed ? 'studio-lint-stat studio-lint-stat-ok' : 'studio-lint-stat studio-lint-stat-warn'
              }
            >
              <span className="studio-lint-stat-num">{report.totalIssues}</span>
              <span className="studio-lint-stat-label">unverified</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.summary.plotUnverified}</span>
              <span className="studio-lint-stat-label">情节</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.summary.relationUnverified}</span>
              <span className="studio-lint-stat-label">关系</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.summary.firstAppearUnverified}</span>
              <span className="studio-lint-stat-label">首登场</span>
            </div>
            <div className="studio-lint-meta">
              {report.passed ? '通过 ✓' : '存疑'} · 情节检 {report.summary.plotChecked} · 关系检{' '}
              {report.summary.relationChecked} · {generatedLabel}
            </div>
          </div>

          <div className="studio-lint-grid">
            <section className="studio-lint-panel">
              <h3 className="studio-lint-panel-title">校验分区</h3>
              <ul className="studio-lint-sections">
                {report.sections.map((sec) => (
                  <li key={sec.id}>
                    <button
                      type="button"
                      className={
                        openSection === sec.id ? 'studio-lint-sec-btn studio-lint-sec-btn-active' : 'studio-lint-sec-btn'
                      }
                      onClick={() => setOpenSection(sec.id)}
                    >
                      <span>{sec.title}</span>
                      <span className={sec.count ? 'studio-lint-badge-warn' : 'studio-lint-badge-ok'}>{sec.count}</span>
                    </button>
                    {sec.checked !== undefined && (
                      <p className="studio-guard-checked">已检 {sec.checked} 条</p>
                    )}
                  </li>
                ))}
              </ul>
            </section>

            <section className="studio-lint-panel studio-lint-detail">
              {active && (
                <>
                  <h3 className="studio-lint-panel-title">
                    {active.title} ({active.count})
                  </h3>
                  {active.count === 0 ? (
                    <p className="studio-lint-empty">本项通过 ✓</p>
                  ) : (
                    <ul className="studio-guard-items">
                      {active.items.map((item, i) => {
                        const eid = entityIdOf(item);
                        const key = `${item.kind}-${eid ?? 'tx'}-${i}`;
                        return (
                          <li key={key} className="studio-guard-item">
                            <div className="studio-guard-item-head">
                              {eid && onOpenEntity ? (
                                <button
                                  type="button"
                                  className="studio-lint-entity-link"
                                  onClick={() => onOpenEntity(eid)}
                                >
                                  {eid}
                                </button>
                              ) : (
                                <span className="studio-guard-entity">{eid ?? '—'}</span>
                              )}
                              <span className={`studio-guard-sev studio-guard-sev-${item.severity}`}>
                                {item.severity}
                              </span>
                            </div>
                            <p className="studio-guard-msg">{item.message}</p>
                            {(item.chapters?.length || item.hint) && (
                              <p className="studio-guard-meta">
                                {item.chapters?.length ? `回目 ${item.chapters.join('、')}` : ''}
                                {item.hint ? ` · ${item.hint}` : ''}
                              </p>
                            )}
                          </li>
                        );
                      })}
                      {active.truncated ? (
                        <li className="studio-lint-more">… 另有 {active.truncated} 条</li>
                      ) : null}
                    </ul>
                  )}
                </>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
