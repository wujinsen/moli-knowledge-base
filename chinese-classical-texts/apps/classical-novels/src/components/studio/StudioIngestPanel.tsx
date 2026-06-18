import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { fetchIngestReport } from '../../lib/studio/client';
import type { BookSlug, IngestReport } from '../../lib/studio/types';
import type { AutoSendPayload } from './StudioTodosBar';
import StudioChapterChatPanel from './StudioChapterChatPanel';

export type ChapterOption = {
  n: number;
  title: string;
};

type Props = {
  book: string;
  bookSlug: BookSlug;
  chapters: ChapterOption[];
  initialChapter?: number;
  initialEditionSlug?: string;
  onOpenEntity?: (entityId: string) => void;
  autoSend?: AutoSendPayload | null;
  onAutoSendDone?: () => void;
};

export default function StudioIngestPanel({
  book,
  bookSlug,
  chapters,
  initialChapter,
  initialEditionSlug,
  onOpenEntity,
  autoSend,
  onAutoSendDone,
}: Props) {
  const defaultChapter = initialChapter ?? chapters[0]?.n ?? 1;
  const [chapter, setChapter] = useState(defaultChapter);
  const [editionSlug, setEditionSlug] = useState(initialEditionSlug ?? '');
  const [query, setQuery] = useState('');
  const [report, setReport] = useState<IngestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialChapter) setChapter(initialChapter);
  }, [initialChapter]);

  useEffect(() => {
    if (initialEditionSlug) setEditionSlug(initialEditionSlug);
  }, [initialEditionSlug]);

  const filtered = useMemo(() => {
    const q = query.trim();
    if (!q) return chapters;
    return chapters.filter(
      (c) => String(c.n).includes(q) || c.title.includes(q),
    );
  }, [chapters, query]);

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchIngestReport(bookSlug, chapter, editionSlug || undefined);
      setReport(data);
    } catch (e) {
      setError((e as Error).message);
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, [bookSlug, chapter, editionSlug]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const pickChapter = (n: number) => {
    setChapter(n);
    const url = new URL(window.location.href);
    url.searchParams.set('chapter', String(n));
    if (editionSlug) url.searchParams.set('edition', editionSlug);
    window.history.replaceState({}, '', url.pathname + url.search);
  };

  const selectedTitle = chapters.find((c) => c.n === chapter)?.title ?? report?.title ?? '';

  return (
    <div className="studio-ingest">
      <div className="studio-ingest-layout">
        <aside className="studio-entity-list" aria-label="选择回目">
          <input
            className="studio-entity-search"
            placeholder="搜索回目…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <ul className="studio-entity-items">
            {filtered.map((c) => (
              <li key={c.n}>
                <button
                  type="button"
                  className={
                    c.n === chapter ? 'studio-entity-btn studio-entity-btn-active' : 'studio-entity-btn'
                  }
                  onClick={() => pickChapter(c.n)}
                >
                  <span>第{c.n}回</span>
                  <span className="studio-entity-type">{c.title.slice(0, 8)}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <div className="studio-ingest-main">
          <div className="studio-ingest-checklist">
            <div className="studio-lint-toolbar">
              <div>
                <h2 className="studio-batch-title">/ingest 摄取 · 第{chapter}回</h2>
                <p className="studio-batch-lead">{selectedTitle}</p>
              </div>
              <div className="studio-ingest-toolbar-actions">
                {bookSlug === 'honglou' && (
                  <select
                    className="studio-ingest-edition"
                    value={editionSlug}
                    aria-label="版本"
                    onChange={(e) => setEditionSlug(e.target.value)}
                  >
                    <option value="">默认</option>
                    <option value="chenggao">程高本</option>
                    <option value="zhiben">脂砚斋本</option>
                  </select>
                )}
                <button
                  type="button"
                  className="studio-btn studio-btn-primary"
                  disabled={loading}
                  onClick={loadReport}
                >
                  {loading ? '加载…' : '刷新清单'}
                </button>
                {report?.readUrl && (
                  <a className="studio-btn studio-btn-ghost" href={report.readUrl}>
                    阅读器 →
                  </a>
                )}
              </div>
            </div>

            {error && <div className="studio-banner studio-banner-error">{error}</div>}

            {report && (
              <div className="studio-ingest-stats">
                <div className="studio-lint-stat">
                  <span className="studio-lint-stat-num">{report.frontmatter.characters}</span>
                  <span className="studio-lint-stat-label">登场人物</span>
                </div>
                <div className="studio-lint-stat">
                  <span className="studio-lint-stat-num">{report.charactersMissingPage?.length ?? 0}</span>
                  <span className="studio-lint-stat-label">缺人物页</span>
                </div>
                <div className="studio-lint-stat">
                  <span className="studio-lint-stat-num">{report.bodyOnlyCharacters?.length ?? 0}</span>
                  <span className="studio-lint-stat-label">正文未列入</span>
                </div>
                <div className="studio-lint-stat">
                  <span className="studio-lint-stat-num">{report.frontmatter.items}</span>
                  <span className="studio-lint-stat-label">名物</span>
                </div>
              </div>
            )}

            {report?.excerpt && (
              <blockquote className="studio-ingest-excerpt">{report.excerpt}</blockquote>
            )}

            {report?.tasks && report.tasks.length > 0 && (
              <ul className="studio-ingest-tasks">
                {report.tasks.map((t) => (
                  <li key={t.id} className={`studio-ingest-task studio-ingest-task--${t.severity}`}>
                    <span>{t.label}</span>
                    {t.entities && t.entities.length > 0 && (
                      <span className="studio-ingest-task-entities">
                        {t.entities.map((id) => {
                          const noPage = report.charactersMissingPage?.includes(id)
                            || report.bodyOnlyCharacters?.includes(id);
                          if (noPage || !onOpenEntity) {
                            return (
                              <span key={id} className="studio-chip">
                                {id}
                              </span>
                            );
                          }
                          return (
                            <button
                              key={id}
                              type="button"
                              className="studio-ingest-entity-link"
                              onClick={() => onOpenEntity(id)}
                            >
                              {id}
                            </button>
                          );
                        })}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <StudioChapterChatPanel
            key={`${chapter}-${editionSlug}`}
            book={book}
            bookSlug={bookSlug}
            chapter={chapter}
            chapterTitle={selectedTitle}
            editionSlug={editionSlug || report?.editionSlug}
            route={`/${bookSlug}/studio?chapter=${chapter}${editionSlug ? `&edition=${editionSlug}` : ''}`}
            autoSend={autoSend}
            onAutoSendDone={onAutoSendDone}
          />
        </div>
      </div>
    </div>
  );
}
