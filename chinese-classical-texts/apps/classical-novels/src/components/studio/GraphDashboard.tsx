import { useCallback, useEffect, useState } from 'react';
import { applyGraphRebuild, fetchGraphPreview } from '../../lib/studio/client';
import type { BookSlug, GraphReport } from '../../lib/studio/types';

type Props = {
  bookSlug: BookSlug;
};

export default function GraphDashboard({ bookSlug }: Props) {
  const [report, setReport] = useState<GraphReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyMsg, setApplyMsg] = useState<string | null>(null);

  const loadPreview = useCallback(async () => {
    setLoading(true);
    setError(null);
    setApplyMsg(null);
    try {
      const data = await fetchGraphPreview(bookSlug);
      setReport(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [bookSlug]);

  useEffect(() => {
    loadPreview();
  }, [loadPreview]);

  const handleApply = async () => {
    if (!report) return;
    const ok = window.confirm(
      `确认重建 ${report.book} 关系图谱？\n\n将写入 ${report.outputPath}` +
        (bookSlug === 'jinpingmei' ? ' 与 src/data/金瓶梅.sna.json' : ''),
    );
    if (!ok) return;

    setApplying(true);
    setError(null);
    setApplyMsg(null);
    try {
      const data = await applyGraphRebuild(bookSlug);
      setReport(data);
      setApplyMsg(
        data.applied
          ? `已写入 ${data.outputPath}` +
              (data.snaPath ? ` · SNA ${data.snaPath}` : '') +
              (data.snaHubs?.length ? ` · Top: ${data.snaHubs.join('、')}` : '')
          : '未完成写盘',
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setApplying(false);
    }
  };

  const generatedLabel = report
    ? new Date(report.generatedAt).toLocaleString('zh-CN', { hour12: false })
    : '';

  return (
    <div className="studio-graph">
      <div className="studio-lint-toolbar">
        <div>
          <h2 className="studio-batch-title">/graph 关系重建</h2>
          <p className="studio-batch-lead">
            扫描人物 frontmatter · 去重 · 校验关系词表 · 输出 <code>src/data/*.relations.json</code>
          </p>
        </div>
        <div className="studio-graph-actions">
          <button type="button" className="studio-btn" disabled={loading || applying} onClick={loadPreview}>
            {loading ? '预览中…' : '刷新预览'}
          </button>
          <button
            type="button"
            className="studio-btn studio-btn-primary"
            disabled={loading || applying || !report || Boolean(report.error)}
            onClick={handleApply}
          >
            {applying ? '重建中…' : '应用重建'}
          </button>
        </div>
      </div>

      {error && <div className="studio-banner studio-banner-error">{error}</div>}
      {applyMsg && <div className="studio-banner studio-banner-ok">{applyMsg}</div>}
      {report?.applied && (
        <div className="studio-banner studio-banner-ok">
          写盘完成 · <a href={`/${bookSlug}/graph`}>打开关系图谱 →</a>
        </div>
      )}

      {report && (
        <>
          <div className="studio-lint-summary">
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.nodeCount}</span>
              <span className="studio-lint-stat-label">节点</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.edgeCount}</span>
              <span className="studio-lint-stat-label">边</span>
            </div>
            <div className="studio-lint-stat">
              <span className="studio-lint-stat-num">{report.characterCount}</span>
              <span className="studio-lint-stat-label">人物/妖怪</span>
            </div>
            <div
              className={
                report.warningCount
                  ? 'studio-lint-stat studio-lint-stat-warn'
                  : 'studio-lint-stat studio-lint-stat-ok'
              }
            >
              <span className="studio-lint-stat-num">{report.warningCount}</span>
              <span className="studio-lint-stat-label">警告</span>
            </div>
            <div className="studio-lint-meta">
              {report.preview && !report.applied ? '预览（未写盘）' : '已写盘'} · {generatedLabel}
            </div>
          </div>

          {report.error && <div className="studio-banner studio-banner-warn">{report.error}</div>}

          <div className="studio-lint-grid">
            <section className="studio-lint-panel">
              <h3 className="studio-lint-panel-title">关系类型分布</h3>
              <ul className="studio-graph-types">
                {report.edgeTypes.map((row) => (
                  <li key={row.type}>
                    <span>{row.type}</span>
                    <span className="studio-lint-badge-ok">{row.count}</span>
                  </li>
                ))}
              </ul>
              {report.contradictionEdges > 0 && (
                <p className="studio-lint-hint">矛盾边（虚线）: {report.contradictionEdges}</p>
              )}
              {report.topicCount > 0 && (
                <p className="studio-lint-hint">版本/矛盾 topic 节点: {report.topicCount}</p>
              )}
              <p className="studio-lint-hint">
                输出: <code>{report.outputPath}</code>
              </p>
            </section>

            <section className="studio-lint-panel studio-lint-detail">
              <h3 className="studio-lint-panel-title">警告 ({report.warningCount})</h3>
              {report.warningCount === 0 ? (
                <p className="studio-lint-empty">词表与目标页校验通过 ✓</p>
              ) : (
                <ul className="studio-lint-lines">
                  {report.warnings.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                  {report.truncatedWarnings ? (
                    <li className="studio-lint-more">… 另有 {report.truncatedWarnings} 条</li>
                  ) : null}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
