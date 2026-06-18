import { useEffect, useMemo, useRef, useState } from 'react';
import { useMaintenanceSession } from '../../lib/studio/useMaintenanceSession';
import type { AutoSendPayload } from './StudioTodosBar';
import type { StudioIntent } from '../../lib/studio/types';
import ChatThread from './ChatThread';
import ContextChips from './ContextChips';
import QuickActions from './QuickActions';

export type StudioChatPanelProps = {
  book: string;
  bookSlug: string;
  entityId: string;
  entityName: string;
  route: string;
  autoSend?: AutoSendPayload | null;
  onAutoSendDone?: () => void;
};

export default function StudioChatPanel({
  book,
  bookSlug,
  entityId,
  entityName,
  route,
  autoSend,
  onAutoSendDone,
}: StudioChatPanelProps) {
  const [input, setInput] = useState('');
  const [applyBusy, setApplyBusy] = useState(false);
  const [applyMessages, setApplyMessages] = useState<Record<string, string>>({});

  const sessionParams = useMemo(
    () => ({
      book: book as '红楼梦' | '金瓶梅' | '西游记',
      bookSlug: bookSlug as 'honglou' | 'jinpingmei' | 'xiyouji',
      page: { kind: 'character' as const, route, entityId, entityType: 'character' as const },
      viewer: { role: 'maintainer' as const },
    }),
    [book, bookSlug, route, entityId],
  );

  const { context, messages, proposals, loading, streaming, error, apiOnline, agentMode, llmModel, send, apply, discard } =
    useMaintenanceSession(sessionParams, Boolean(entityId));

  const autoSentRef = useRef(false);
  useEffect(() => {
    autoSentRef.current = false;
  }, [entityId]);

  useEffect(() => {
    if (!autoSend || !context || streaming || loading || autoSentRef.current) return;
    autoSentRef.current = true;
    send(autoSend.text, autoSend.intent ? { type: autoSend.intent as StudioIntent } : undefined);
    onAutoSendDone?.();
  }, [autoSend, context, streaming, loading, send, onAutoSendDone]);

  const handleSend = () => {
    if (!input.trim()) return;
    send(input);
    setInput('');
  };

  const handleQuick = (intent: StudioIntent, prompt: string) => {
    send(prompt, { type: intent });
  };

  const handleApply = async (id: string) => {
    setApplyBusy(true);
    try {
      const res = await apply(id);
      if (res?.message) {
        setApplyMessages((m) => ({ ...m, [id]: res.message! }));
      }
    } finally {
      setApplyBusy(false);
    }
  };

  return (
    <div className="studio-chat-panel">
      <header className="studio-panel-head">
        <div>
          <h2 className="studio-drawer-title">{entityName} · 实体维护</h2>
          <p className="studio-drawer-sub">信物 / 服饰 · 聊天 + 变更卡片</p>
        </div>
        <a className="studio-panel-link" href={`/${bookSlug}/c/${entityId}`}>
          查看人物页 →
        </a>
      </header>

      {apiOnline === false && (
        <div className="studio-banner studio-banner-warn">
          Orchestrator 未启动。请运行：<code>npm run studio:api</code>
        </div>
      )}

      {apiOnline && agentMode && (
        <div className="studio-banner studio-agent-badge" data-pagefind-ignore>
          {agentMode === 'llm' && llmModel ? (
            <>LLM · <code>{llmModel}</code></>
          ) : (
            <>Mock 模式 · 设置 <code>STUDIO_LLM_API_KEY</code> 启用真实 LLM</>
          )}
        </div>
      )}

      {loading && <div className="studio-banner">加载上下文…</div>}
      {error && <div className="studio-banner studio-banner-error">{error}</div>}

      {context && <ContextChips context={context} bookSlug={bookSlug} />}

      <ChatThread
        messages={messages}
        proposals={proposals}
        bookSlug={bookSlug}
        onApply={handleApply}
        onDiscard={discard}
        applyBusy={applyBusy}
        applyMessages={applyMessages}
      />

      <footer className="studio-drawer-foot">
        <QuickActions disabled={streaming || loading || !context} onAction={handleQuick} />
        <div className="studio-input-row">
          <input
            className="studio-input"
            placeholder="例：第73回补信物链…"
            value={input}
            disabled={streaming || !context}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button
            type="button"
            className="studio-btn studio-btn-primary"
            disabled={streaming || !context || !input.trim()}
            onClick={handleSend}
          >
            发送
          </button>
        </div>
      </footer>
    </div>
  );
}
