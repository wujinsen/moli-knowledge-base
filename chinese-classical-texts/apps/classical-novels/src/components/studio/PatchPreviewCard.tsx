import { useState } from 'react';
import type { PatchProposal } from '../../lib/studio/types';

type Props = {
  proposal: PatchProposal;
  bookSlug: string;
  onApply: (id: string) => Promise<{ message?: string } | void>;
  onDiscard: (id: string) => void;
  busy?: boolean;
  applyMessage?: string;
};

export default function PatchPreviewCard({
  proposal,
  bookSlug,
  onApply,
  onDiscard,
  busy,
  applyMessage,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const guard = proposal.guardPreview?.status ?? 'skipped';
  const patchCount = proposal.patches?.length ?? 0;
  const applied = proposal.status === 'applied' || proposal.status === 'partially_applied';

  return (
    <div className="studio-proposal">
      <div className="studio-proposal-head">
        <strong>{proposal.title}</strong>
        <span className={`studio-guard studio-guard--${guard}`}>{guard}</span>
      </div>
      <p className="studio-proposal-summary">{proposal.summary}</p>
      {proposal.sources?.[0] && (
        <p className="studio-proposal-source">
          依据：
          <a href={proposal.sources[0].readUrl ?? '#'}>
            第{proposal.sources[0].chapter}回
          </a>
        </p>
      )}
      <p className="studio-proposal-meta">{patchCount} 个文件变更</p>
      {expanded && (
        <ul className="studio-patch-list">
          {(proposal.patches ?? []).map((p) => (
            <li key={p.path}>
              <code>{p.path}</code>
              {p.hunkSummary && <span> — {p.hunkSummary}</span>}
            </li>
          ))}
        </ul>
      )}
      <div className="studio-proposal-actions">
        <button type="button" className="studio-btn studio-btn-ghost" onClick={() => setExpanded((v) => !v)}>
          {expanded ? '收起' : '展开 diff 列表'}
        </button>
        {!applied && (
          <>
            <button
              type="button"
              className="studio-btn studio-btn-primary"
              disabled={busy || !proposal.actions.canApply}
              title={proposal.actions.canApply ? undefined : 'MVP 占位 proposal 不可应用'}
              onClick={() => onApply(proposal.proposalId)}
            >
              应用全部
            </button>
            <button
              type="button"
              className="studio-btn studio-btn-ghost"
              disabled={busy}
              onClick={() => onDiscard(proposal.proposalId)}
            >
              丢弃
            </button>
          </>
        )}
        {applied && (
          <span className="studio-applied">{applyMessage ?? '已写盘并完成 postApply'}</span>
        )}
      </div>
    </div>
  );
}
