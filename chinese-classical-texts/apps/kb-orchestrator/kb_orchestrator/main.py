from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .apply import execute_apply
from .config import NOVELS_ROOT
from .context import build_maintenance_context
from .dream_runner import (
    DreamRunError,
    apply_dream_tier,
    dream_catalog,
    preview_dream_tier,
    stream_dream_apply,
    stream_dream_preview,
)
from .graph_runner import GraphRunError, apply_graph, preview_graph
from .guard_runner import GuardRunError, run_guard_report
from .ingest_runner import IngestRunError, run_ingest_report
from .lint_runner import LintRunError, run_lint_report
from .todos_runner import TodosRunError, run_studio_todos
from .agent import run_agent_turn
from .config import STUDIO_LLM_MODEL, agent_mode, llm_configured
from .patch import PatchError
from .storage import store

app = FastAPI(title="kb-orchestrator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PageRef(BaseModel):
    kind: str = "character"
    route: str
    entityId: str
    entityType: str | None = None
    editionSlug: str | None = None


class CreateSessionBody(BaseModel):
    book: str
    bookSlug: str
    locale: str = "zh-CN"
    page: PageRef
    viewer: dict[str, str] | None = None


class IntentHint(BaseModel):
    type: str
    params: dict[str, Any] | None = None


class SendMessageBody(BaseModel):
    text: str = ""
    clientMessageId: str | None = None
    intentHint: IntentHint | None = None


class ApplyBody(BaseModel):
    patchPaths: list[str] | None = None
    skipPostApply: bool = False


class GraphApplyBody(BaseModel):
    confirm: bool = True


class DreamApplyBody(BaseModel):
    confirm: bool = True


@app.get("/api/studio/health")
def health() -> dict:
    mode = agent_mode()
    return {
        "status": "ok",
        "novelsRoot": str(NOVELS_ROOT),
        "novelsRootExists": NOVELS_ROOT.is_dir(),
        "mode": "apply",
        "agentMode": mode,
        "llmConfigured": llm_configured(),
        "llmModel": STUDIO_LLM_MODEL if llm_configured() else None,
    }


@app.get("/api/studio/lint/{book_slug}")
def lint_report(book_slug: str) -> dict:
    try:
        return run_lint_report(book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LintRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/studio/graph/{book_slug}")
def graph_preview(book_slug: str) -> dict:
    try:
        return preview_graph(book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except GraphRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/studio/graph/{book_slug}")
def graph_apply(book_slug: str, body: GraphApplyBody) -> dict:
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")
    try:
        return apply_graph(book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except GraphRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/studio/dream/{book_slug}")
def dream_status(book_slug: str) -> dict:
    try:
        return dream_catalog(book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DreamRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/studio/dream/{book_slug}/{tier_id}")
def dream_preview(book_slug: str, tier_id: str) -> dict:
    try:
        return preview_dream_tier(book_slug, tier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DreamRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/studio/dream/{book_slug}/{tier_id}")
def dream_apply(book_slug: str, tier_id: str, body: DreamApplyBody) -> dict:
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")
    try:
        return apply_dream_tier(book_slug, tier_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except DreamRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/studio/dream/{book_slug}/{tier_id}/preview/stream")
async def dream_preview_stream(book_slug: str, tier_id: str):
    return StreamingResponse(
        stream_dream_preview(book_slug, tier_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/studio/dream/{book_slug}/{tier_id}/apply/stream")
async def dream_apply_stream(book_slug: str, tier_id: str, body: DreamApplyBody):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")
    return StreamingResponse(
        stream_dream_apply(book_slug, tier_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/studio/guard/{book_slug}")
def guard_report(book_slug: str) -> dict:
    try:
        return run_guard_report(book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except GuardRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/studio/ingest/{book_slug}/{chapter}")
def ingest_report(book_slug: str, chapter: int, edition: str | None = None) -> dict:
    try:
        return run_ingest_report(book_slug, chapter, edition)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except IngestRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/studio/todos/{book_slug}")
def studio_todos(book_slug: str) -> dict:
    try:
        return run_studio_todos(book_slug)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except TodosRunError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/studio/sessions")
def create_session(body: CreateSessionBody) -> dict:
    try:
        ctx = build_maintenance_context(
            book_slug=body.bookSlug,
            page_kind=body.page.kind,
            entity_id=body.page.entityId,
            route=body.page.route,
            edition_slug=body.page.editionSlug,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    store.create(ctx)
    return ctx


@app.get("/api/studio/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    s = store.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="session not found")
    return s.context


@app.get("/api/studio/proposals/{proposal_id}")
def get_proposal(proposal_id: str) -> dict:
    hit = store.get_proposal(proposal_id)
    if not hit:
        raise HTTPException(status_code=404, detail="proposal not found")
    return hit[1]


@app.post("/api/studio/proposals/{proposal_id}/apply")
def apply_proposal(proposal_id: str, body: ApplyBody) -> dict:
    hit = store.get_proposal(proposal_id)
    if not hit:
        raise HTTPException(status_code=404, detail="proposal not found")
    session, proposal = hit
    if proposal.get("status") in ("applied", "partially_applied"):
        raise HTTPException(status_code=400, detail="proposal already applied")
    if not proposal.get("actions", {}).get("canApply"):
        raise HTTPException(status_code=400, detail="proposal not applicable (empty patches)")

    book = session.context.get("book") or "红楼梦"
    try:
        result = execute_apply(
            book=book,
            proposal=proposal,
            patch_paths=body.patchPaths,
            skip_post_apply=body.skipPostApply,
        )
    except PatchError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    proposal["status"] = result.get("status", "applied")
    return result


@app.post("/api/studio/proposals/{proposal_id}/discard")
def discard_proposal(proposal_id: str) -> dict:
    hit = store.get_proposal(proposal_id)
    if not hit:
        raise HTTPException(status_code=404, detail="proposal not found")
    _session, proposal = hit
    proposal["status"] = "discarded"
    return {"proposalId": proposal_id, "status": "discarded"}


async def _sse_message_stream(session_id: str, text: str, intent_hint: dict | None):
    s = store.get(session_id)
    if not s:
        yield f"event: error\ndata: {json.dumps({'code': 'not_found', 'message': 'session not found'}, ensure_ascii=False)}\n\n"
        return

    ctx = s.context
    tool_events: list[tuple[str, dict]] = []

    def on_event(event: str, data: dict) -> None:
        tool_events.append((event, data))

    reply, proposal = await asyncio.to_thread(
        run_agent_turn,
        ctx,
        text,
        intent_hint,
        s.messages,
        on_event,
    )

    for event, data in tool_events:
        yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    chunk_size = 24
    for i in range(0, len(reply), chunk_size):
        part = reply[i : i + chunk_size]
        yield f"event: message.delta\ndata: {json.dumps({'text': part}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.02)

    msg_id = f"msg_{session_id[-8:]}"
    s.messages.append({"role": "user", "text": text})
    s.messages.append({"role": "assistant", "text": reply, "messageId": msg_id})
    yield f"event: message.done\ndata: {json.dumps({'messageId': msg_id, 'role': 'assistant'}, ensure_ascii=False)}\n\n"

    if proposal:
        store.add_proposal(session_id, proposal)
        yield f"event: proposal.ready\ndata: {json.dumps(proposal, ensure_ascii=False)}\n\n"
        gp = proposal.get("guardPreview")
        if gp:
            yield f"event: guard.result\ndata: {json.dumps(gp, ensure_ascii=False)}\n\n"


@app.post("/api/studio/sessions/{session_id}/messages")
async def send_message(session_id: str, body: SendMessageBody):
    intent = body.intentHint.model_dump() if body.intentHint else None
    return StreamingResponse(
        _sse_message_stream(session_id, body.text, intent),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
