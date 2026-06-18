import { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchLintReport } from '../../lib/studio/client';
import type { BookSlug, LintReport, LintSection } from '../../lib/studio/types';

type Props = {
  bookSlug: BookSlug;
  onOpenEntity?: (entityId: string) => void;
};

const GROUP_LABEL: Record<string, string> = {
  core: '核心',
  items: '名物百科',
  places: '建筑图鉴',
  shi: '诗词意象',
};

function entityFromLine(line: string): string | null {
  const patterns = [
    /^(?:no summary|no first_appear):\s*(.+)$/,
    /^(?:缺实体页|字段缺漏|名物孤儿|意象孤儿|parent 缺页|nearby 缺页|crosslinks 未链|缺 inference 人物边|缺 inference 边|inference 缺 phase|inference 缺 temperature|五行标签不符|互文链缺节点):\s*(.+?)(?:\s*[·(@]|$)/,
    /^(?:缺核心五行符号):\s*(.+)$/,
    /^([^:]+):\s/m,
  ];
  for (const re of patterns) {
    const m = line.match(re);
    const id = m?.[1]?.trim();
    if (id && !id.includes('(') && id.length <= 40) return id;
  }
  return null;
}

function sectionsByGroup(sections: LintSection[]): { group: string; label: string; sections: LintSection[] }[] {
  const order = ['core', 'items', 'places', 'shi'];
  const map = new Map<string, LintSection[]>();
  for (const sec of sections) {
    const g = sec.group ?? 'core';
    if (!map.has(g)) map.set(g, []);
    map.get(g)!.push(sec);
  }
  return order
    .filter((g) => map.has(g))
    .map((g) => ({ group: g, label: GROUP_LABEL[g] ?? g, sections: map.get(g)! }));
}

export default function LintDashboard({ bookSlug, onOpenEntity }: Props) {
  const [report, setReport] = useState<LintReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSection, setOpenSection] = useState<string | null>('character_fields');

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLintReport(bookSlug);
      setReport(data);
      const first = data.sections.find((s) => s.count > 0);
      setOpenSection(first?.id ?? 'density');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [bookSlug]);

  useEffect(() => {
    run();
  }, [run]);

  const scoreMax = useMemo(() => {
    if (!report) return 1;
    return Math.max(...Object.values(report.density.scoreDistribution), 1);
  }, [report]);

  const grouped = useMemo(() => (report ? sectionsByGroup(report.sections) : []), [report]);

  const generatedLabel = report
    ? new Date(report.generatedAt).toLocaleString('zh-CN', { hour12: false })
    : '';

  return (
    <div className="studio-lint">
      <div className="studio-lint-toolbar">
        <div>
          <h2 className="studio-batch-title">/lint 体检</h2>
          <p className="studio-batch-lead">
            只报告、不改写。核心（人物/回目）+ 名物 · 建筑 · 诗词意象模块。
          </p>
        </div>
        <button type="button" className="studio-btn studio-btn-primary" disabled={loading} onClick={run}>
          {loading ? '扫描中…' : '重新扫描'}
        </button>
      </div>

      {error && <div className="studio-banner studio-banner-error">{error}</div>}

      {report && (
        <>
          <div className="studio-lint-summary">
            <div className={`studio-lint-stat ${report.passed ? 'studio-lint-stat-ok' : 'studio-lint-stat-warn'}`}>
              <span className="studio-lint-stat-num">{report.totalIssues}</span>
              <span className="studio-lint-stat-label">结构问题</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.density.totalCharacters}</span>
              <span className="studio-lint-stat-label">人物页</span>
            </div>
            {report.moduleStats?.items && (
              <div className="studio-lint-stat">
                <span className="studio-lint-stat-num">{report.moduleStats.items.count}</span>
                <span className="studio-lint-stat-label">名物</span>
              </div>
            )}
            {report.moduleStats?.places && (
              <div className="studio-lint-stat">
                <span className="studio-lint-stat-num">{report.moduleStats.places.count}</span>
                <span className="studio-lint-stat-label">建筑</span>
              </div>
            )}
            {report.moduleStats?.shi && (
              <div className="studio-lint-stat">
                <span className="studio-lint-stat-num">{report.moduleStats.shi.count}</span>
                <span className="studio-lint-stat-label">意象</span>
              </div>
            )}
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.density.priorityBatch.length}</span>
              <span className="studio-lint-stat-label">低密度优先</span>
            </div>
            <div className="studio-lint-meta">生成于 {generatedLabel}</div>
          </div>

          <div className="studio-lint-grid">
            <section className="studio-lint-panel">
              <h3 className="studio-lint-panel-title">规则检查</h3>
              <ul className="studio-lint-sections">
                {grouped.map(({ group, label, sections }) => (
                  <li key={group}>
                    <div className="studio-lint-group-label">{label}</div>
                    <ul className="studio-lint-sections-nested">
                      {sections.map((sec) => (
                        <li key={sec.id}>
                          <button
                            type="button"
                            className={
                              openSection === sec.id
                                ? 'studio-lint-sec-btn studio-lint-sec-btn-active'
                                : 'studio-lint-sec-btn'
                            }
                            onClick={() => setOpenSection(sec.id)}
                          >
                            <span>{sec.title}</span>
                            <span className={sec.count ? 'studio-lint-badge-warn' : 'studio-lint-badge-ok'}>
                              {sec.count}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </li>
                ))}
                <li>
                  <div className="studio-lint-group-label">人物</div>
                  <button
                    type="button"
                    className={
                      openSection === 'density' ? 'studio-lint-sec-btn studio-lint-sec-btn-active' : 'studio-lint-sec-btn'
                    }
                    onClick={() => setOpenSection('density')}
                  >
                    <span>密度分带</span>
                    <span className="studio-lint-badge-ok">{report.density.totalCharacters}</span>
                  </button>
                </li>
              </ul>
            </section>

            <section className="studio-lint-panel studio-lint-detail">
              {openSection === 'density' ? (
                <>
                  <h3 className="studio-lint-panel-title">score 分布</h3>
                  <p className="studio-lint-hint">
                    score = rel×2 + plot×3 + 主要关系 + 评析 + min(入链,5) · 图谱{' '}
                    {report.density.graphNodes}/{report.density.graphEdges}
                  </p>
                  <div className="studio-score-bars">
                    {Object.entries(report.density.scoreDistribution).map(([score, count]) => (
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

                  <h4 className="studio-lint-subtitle">下一批优先 (score≤8)</h4>
                  <ul className="studio-lint-entity-list">
                    {report.density.priorityBatch.map((row) => (
                      <li key={row.id}>
                        {onOpenEntity ? (
                          <button type="button" className="studio-lint-entity-link" onClick={() => onOpenEntity(row.id)}>
                            {row.id}
                          </button>
                        ) : (
                          <span>{row.id}</span>
                        )}
                        <span className="studio-lint-entity-meta">
                          score={row.score} · {row.flags.join(' · ') || '—'}
                        </span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <>
                  {(() => {
                    const sec = report.sections.find((s) => s.id === openSection);
                    if (!sec) return null;
                    return (
                      <>
                        <h3 className="studio-lint-panel-title">
                          {sec.title} ({sec.count})
                        </h3>
                        {sec.count === 0 ? (
                          <p className="studio-lint-empty">本项通过 ✓</p>
                        ) : (
                          <ul className="studio-lint-lines">
                            {sec.items.map((line) => {
                              const eid = entityFromLine(line);
                              return (
                                <li key={line}>
                                  {eid && onOpenEntity ? (
                                    <button
                                      type="button"
                                      className="studio-lint-entity-link"
                                      onClick={() => onOpenEntity(eid)}
                                    >
                                      {line}
                                    </button>
                                  ) : (
                                    line
                                  )}
                                </li>
                              );
                            })}
                            {sec.truncated ? <li className="studio-lint-more">… 另有 {sec.truncated} 条</li> : null}
                          </ul>
                        )}
                      </>
                    );
                  })()}
                </>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
