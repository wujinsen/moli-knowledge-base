from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    session_id: str
    context: dict
    messages: list[dict] = field(default_factory=list)
    proposals: dict[str, dict] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, context: dict) -> Session:
        sid = context["sessionId"]
        s = Session(session_id=sid, context=context)
        self._sessions[sid] = s
        return s

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def add_proposal(self, session_id: str, proposal: dict) -> None:
        s = self._sessions[session_id]
        s.proposals[proposal["proposalId"]] = proposal

    def get_proposal(self, proposal_id: str) -> tuple[Session, dict] | None:
        for s in self._sessions.values():
            if proposal_id in s.proposals:
                return s, s.proposals[proposal_id]
        return None


store = SessionStore()
