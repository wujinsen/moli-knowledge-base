import { useEffect, useMemo, useState } from 'react';
import StudioChatPanel from './StudioChatPanel';
import StudioBatchPanel from './StudioBatchPanel';
import StudioIngestPanel, { type ChapterOption } from './StudioIngestPanel';
import StudioTodosBar, { type AutoSendPayload } from './StudioTodosBar';
import type { BookSlug, StudioTodo } from '../../lib/studio/types';

export type StudioEntity = {
  id: string;
  name: string;
  type: 'character' | 'monster';
};

export type StudioWorkspaceProps = {
  book: string;
  bookSlug: string;
  entities: StudioEntity[];
  chapters: ChapterOption[];
  initialEntityId?: string;
  initialChapter?: number;
  initialEditionSlug?: string;
};

type StudioTab = 'workspace' | 'ingest' | 'batch';

const demoBySlug: Record<string, string> = {
  honglou: '贾迎春',
  jinpingmei: '西门庆',
  xiyouji: '孙悟空',
};

export default function StudioWorkspace({
  book,
  bookSlug,
  entities,
  chapters,
  initialEntityId,
  initialChapter,
  initialEditionSlug,
}: StudioWorkspaceProps) {
  const defaultId = demoBySlug[bookSlug] ?? entities[0]?.id ?? '';
  const [tab, setTab] = useState<StudioTab>(initialChapter ? 'ingest' : 'workspace');
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState(initialEntityId || defaultId);
  const [ingestChapter, setIngestChapter] = useState(initialChapter);
  const [ingestEdition, setIngestEdition] = useState(initialEditionSlug);
  const [autoSend, setAutoSend] = useState<AutoSendPayload | null>(null);

  useEffect(() => {
    if (initialEntityId) {
      setSelectedId(initialEntityId);
      setTab('workspace');
    }
  }, [initialEntityId]);

  useEffect(() => {
    if (initialChapter) setTab('ingest');
  }, [initialChapter]);

  const sorted = useMemo(
    () => [...entities].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN')),
    [entities],
  );

  const filtered = useMemo(() => {
    const q = query.trim();
    if (!q) return sorted;
    return sorted.filter(
      (e) => e.id.includes(q) || e.name.includes(q),
    );
  }, [query, sorted]);

  const selected = entities.find((e) => e.id === selectedId) ?? entities[0];

  const pickEntity = (id: string) => {
    setSelectedId(id);
    setTab('workspace');
    const url = new URL(window.location.href);
    url.searchParams.set('entity', id);
    window.history.replaceState({}, '', url.pathname + url.search);
  };

  const openEntityFromLint = (id: string) => {
    pickEntity(id);
  };

  const openEntityFromIngest = (id: string) => {
    pickEntity(id);
  };

  const handleTodo = (todo: StudioTodo) => {
    setAutoSend({ text: todo.suggestedPrompt, intent: todo.kind });
    if (todo.kind === 'ingest_chapter' && todo.chapter) {
      setTab('ingest');
      setIngestChapter(todo.chapter);
      if (todo.editionSlug) setIngestEdition(todo.editionSlug);
      const url = new URL(window.location.href);
      url.searchParams.delete('entity');
      url.searchParams.set('chapter', String(todo.chapter));
      if (todo.editionSlug) url.searchParams.set('edition', todo.editionSlug);
      window.history.replaceState({}, '', url.pathname + url.search);
      return;
    }
    if (todo.entityId) {
      pickEntity(todo.entityId);
    }
  };

  const clearAutoSend = () => setAutoSend(null);

  return (
    <div className="studio-workspace">
      <header className="studio-workspace-head">
        <div>
          <h1 className="studio-workspace-title">维护台 · Studio</h1>
          <p className="studio-workspace-lead">
            知识库自我进化模块 — 对应 AGENTS.md 的 ingest / query / lint / dream / graph / guard。
          </p>
        </div>
        <div className="studio-workspace-head-actions">
          <StudioTodosBar bookSlug={bookSlug as BookSlug} onTodo={handleTodo} />
          <div className="studio-tab-bar" role="tablist" aria-label="维护台分区">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'workspace'}
            className={tab === 'workspace' ? 'studio-tab studio-tab-active' : 'studio-tab'}
            onClick={() => setTab('workspace')}
          >
            实体工作区
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'ingest'}
            className={tab === 'ingest' ? 'studio-tab studio-tab-active' : 'studio-tab'}
            onClick={() => setTab('ingest')}
          >
            摄取
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'batch'}
            className={tab === 'batch' ? 'studio-tab studio-tab-active' : 'studio-tab'}
            onClick={() => setTab('batch')}
          >
            批处理
          </button>
          </div>
        </div>
      </header>

      {tab === 'workspace' ? (
        <div className="studio-workspace-body">
          <aside className="studio-entity-list" aria-label="选择维护对象">
            <input
              className="studio-entity-search"
              placeholder="搜索人物…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <ul className="studio-entity-items">
              {filtered.map((e) => (
                <li key={e.id}>
                  <button
                    type="button"
                    className={
                      e.id === selected?.id ? 'studio-entity-btn studio-entity-btn-active' : 'studio-entity-btn'
                    }
                    onClick={() => pickEntity(e.id)}
                  >
                    <span>{e.name}</span>
                    <span className="studio-entity-type">{e.type === 'monster' ? '妖怪' : '人物'}</span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          {selected ? (
            <StudioChatPanel
              key={selected.id}
              book={book}
              bookSlug={bookSlug}
              entityId={selected.id}
              entityName={selected.name}
              route={`/${bookSlug}/studio?entity=${encodeURIComponent(selected.id)}`}
              autoSend={autoSend}
              onAutoSendDone={clearAutoSend}
            />
          ) : (
            <div className="studio-empty">暂无实体，请从左侧选择。</div>
          )}
        </div>
      ) : tab === 'ingest' ? (
        <StudioIngestPanel
          key={`ingest-${ingestChapter ?? 1}-${ingestEdition ?? ''}`}
          book={book}
          bookSlug={bookSlug as BookSlug}
          chapters={chapters}
          initialChapter={ingestChapter}
          initialEditionSlug={ingestEdition}
          onOpenEntity={openEntityFromIngest}
          autoSend={autoSend}
          onAutoSendDone={clearAutoSend}
        />
      ) : (
        <StudioBatchPanel bookSlug={bookSlug as BookSlug} onOpenEntity={openEntityFromLint} />
      )}

      <footer className="studio-workspace-foot">
        <span>本地 dev：终端 A <code>npm run studio:api</code> · 终端 B <code>npm run dev</code></span>
        <span>协议 <code>docs/维护台-聊天协议.md</code></span>
      </footer>
    </div>
  );
}
