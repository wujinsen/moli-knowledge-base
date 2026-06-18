import { useCallback, useEffect, useRef, useState } from 'react';
import {
  applyProposal,
  createSession,
  discardProposal,
  sendMessageSSE,
  studioHealth,
} from '../../lib/studio/client';
import type {
  CreateSessionRequest,
  MaintenanceContext,
  PatchProposal,
  StudioIntent,
} from '../../lib/studio/types';

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  streaming?: boolean;
};

export function useMaintenanceSession(params: CreateSessionRequest | null, enabled: boolean) {
  const [context, setContext] = useState<MaintenanceContext | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [proposals, setProposals] = useState<PatchProposal[]>([]);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [agentMode, setAgentMode] = useState<string | null>(null);
  const [llmModel, setLlmModel] = useState<string | null>(null);
  const streamRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    studioHealth()
      .then((h) => {
        setApiOnline(h.status === 'ok' && h.novelsRootExists);
        setAgentMode(h.agentMode ?? null);
        setLlmModel(h.llmModel ?? null);
      })
      .catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    if (!enabled || !params) return;
    setLoading(true);
    setError(null);
    createSession(params)
      .then((ctx) => {
        setContext(ctx);
        const isChapter = ctx.page.kind === 'chapter';
        const welcome = isChapter
          ? `摄取助手已就绪。当前：**${ctx.page.name ?? `第${ctx.page.entityId}回`}**。${
              ctx.lintHints?.[0]?.message ? `提示：${ctx.lintHints[0].message}` : ''
            }`
          : `维护助手已就绪。当前：**${ctx.page.name ?? ctx.page.entityId}**。${
              ctx.lintHints?.[0]?.message ? `提示：${ctx.lintHints[0].message}` : ''
            }`;
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            text: welcome,
          },
        ]);
        setProposals([]);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));

    return () => {
      streamRef.current?.();
    };
  }, [enabled, params?.page.entityId, params?.page.kind, params?.bookSlug, params?.page.editionSlug]);

  const send = useCallback(
    (text: string, intentHint?: { type: StudioIntent; params?: Record<string, unknown> }) => {
      if (!context?.sessionId || streaming) return;
      const trimmed = text.trim();
      if (!trimmed && !intentHint) return;

      const userMsg: ChatMessage = {
        id: `u_${Date.now()}`,
        role: 'user',
        text: trimmed || `[${intentHint?.type}]`,
      };
      const assistantId = `a_${Date.now()}`;
      setMessages((m) => [...m, userMsg, { id: assistantId, role: 'assistant', text: '', streaming: true }]);
      setStreaming(true);
      setError(null);

      streamRef.current?.();
      streamRef.current = sendMessageSSE(
        context.sessionId,
        { text: trimmed, intentHint },
        (ev) => {
          if (ev.event === 'message.delta') {
            setMessages((m) =>
              m.map((msg) =>
                msg.id === assistantId ? { ...msg, text: msg.text + ev.data.text } : msg,
              ),
            );
          }
          if (ev.event === 'message.done') {
            setMessages((m) =>
              m.map((msg) => (msg.id === assistantId ? { ...msg, streaming: false } : msg)),
            );
            setStreaming(false);
          }
          if (ev.event === 'proposal.ready') {
            setProposals((p) => [...p, ev.data]);
          }
          if (ev.event === 'error') {
            setError(ev.data.message);
          }
        },
        (err) => {
          setError(err.message);
          setStreaming(false);
        },
      );
    },
    [context?.sessionId, streaming],
  );

  const apply = useCallback(async (proposalId: string) => {
    setError(null);
    try {
      const res = await applyProposal(proposalId);
      setProposals((p) =>
        p.map((x) =>
          x.proposalId === proposalId
            ? { ...x, status: (res.status === 'failed' ? x.status : res.status) as PatchProposal['status'] }
            : x,
        ),
      );
      return res;
    } catch (e) {
      setError((e as Error).message);
      throw e;
    }
  }, []);

  const discard = useCallback(async (proposalId: string) => {
    await discardProposal(proposalId);
    setProposals((p) => p.filter((x) => x.proposalId !== proposalId));
  }, []);

  return {
    context,
    messages,
    proposals,
    loading,
    streaming,
    error,
    apiOnline,
    agentMode,
    llmModel,
    send,
    apply,
    discard,
  };
}
