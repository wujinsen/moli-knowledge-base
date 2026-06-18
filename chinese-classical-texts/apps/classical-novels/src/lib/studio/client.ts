import type {
  ApplyProposalRequest,
  ApplyProposalResponse,
  CreateSessionRequest,
  LintReport,
  GraphReport,
  DreamCatalog,
  DreamTierPreview,
  GuardReport,
  IngestReport,
  MaintenanceContext,
  PatchProposal,
  SendMessageRequest,
  StudioSSEEvent,
  StudioTodosReport,
} from './types';

const API_BASE = import.meta.env.PUBLIC_STUDIO_API ?? '';

async function parseError(res: Response): Promise<string> {
  try {
    const j = await res.json();
    return j.detail ?? j.message ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function studioHealth(): Promise<{
  status: string;
  novelsRootExists: boolean;
  agentMode?: string;
  llmConfigured?: boolean;
  llmModel?: string | null;
}> {
  const res = await fetch(`${API_BASE}/api/studio/health`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchLintReport(bookSlug: string): Promise<LintReport> {
  const res = await fetch(`${API_BASE}/api/studio/lint/${encodeURIComponent(bookSlug)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchGraphPreview(bookSlug: string): Promise<GraphReport> {
  const res = await fetch(`${API_BASE}/api/studio/graph/${encodeURIComponent(bookSlug)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function applyGraphRebuild(bookSlug: string): Promise<GraphReport> {
  const res = await fetch(`${API_BASE}/api/studio/graph/${encodeURIComponent(bookSlug)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirm: true }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchDreamCatalog(bookSlug: string): Promise<DreamCatalog> {
  const res = await fetch(`${API_BASE}/api/studio/dream/${encodeURIComponent(bookSlug)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchDreamPreview(bookSlug: string, tierId: string): Promise<DreamTierPreview> {
  const res = await fetch(
    `${API_BASE}/api/studio/dream/${encodeURIComponent(bookSlug)}/${encodeURIComponent(tierId)}`,
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function applyDreamTier(bookSlug: string, tierId: string): Promise<DreamTierPreview> {
  const res = await fetch(
    `${API_BASE}/api/studio/dream/${encodeURIComponent(bookSlug)}/${encodeURIComponent(tierId)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirm: true }),
    },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchGuardReport(bookSlug: string): Promise<GuardReport> {
  const res = await fetch(`${API_BASE}/api/studio/guard/${encodeURIComponent(bookSlug)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchIngestReport(
  bookSlug: string,
  chapter: number,
  editionSlug?: string,
): Promise<IngestReport> {
  const q = editionSlug ? `?edition=${encodeURIComponent(editionSlug)}` : '';
  const res = await fetch(
    `${API_BASE}/api/studio/ingest/${encodeURIComponent(bookSlug)}/${chapter}${q}`,
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function fetchStudioTodos(bookSlug: string): Promise<StudioTodosReport> {
  const res = await fetch(`${API_BASE}/api/studio/todos/${encodeURIComponent(bookSlug)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function createSession(body: CreateSessionRequest): Promise<MaintenanceContext> {
  const res = await fetch(`${API_BASE}/api/studio/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function getProposal(proposalId: string): Promise<PatchProposal> {
  const res = await fetch(`${API_BASE}/api/studio/proposals/${encodeURIComponent(proposalId)}`);
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function applyProposal(
  proposalId: string,
  body: ApplyProposalRequest = {},
): Promise<ApplyProposalResponse & { message?: string }> {
  const res = await fetch(`${API_BASE}/api/studio/proposals/${encodeURIComponent(proposalId)}/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function discardProposal(proposalId: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/api/studio/proposals/${encodeURIComponent(proposalId)}/discard`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export function sendMessageSSE(
  sessionId: string,
  body: SendMessageRequest,
  onEvent: (ev: StudioSSEEvent) => void,
  onError: (err: Error) => void,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/studio/sessions/${encodeURIComponent(sessionId)}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(await parseError(res));
      if (!res.body) throw new Error('empty stream');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const block of parts) {
          const lines = block.split('\n');
          let event = 'message';
          let data = '';
          for (const line of lines) {
            if (line.startsWith('event:')) event = line.slice(6).trim();
            if (line.startsWith('data:')) data = line.slice(5).trim();
          }
          if (!data) continue;
          const parsed = JSON.parse(data);
          onEvent({ event, data: parsed } as StudioSSEEvent);
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') onError(e as Error);
    }
  })();

  return () => controller.abort();
}
