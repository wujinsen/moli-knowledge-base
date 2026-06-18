import type { ChatMessage } from '../../lib/studio/useMaintenanceSession';
import type { PatchProposal } from '../../lib/studio/types';
import PatchPreviewCard from './PatchPreviewCard';

type Props = {
  messages: ChatMessage[];
  proposals: PatchProposal[];
  bookSlug: string;
  onApply: (id: string) => Promise<{ message?: string } | void>;
  onDiscard: (id: string) => void;
  applyBusy?: boolean;
  applyMessages?: Record<string, string>;
};

export default function ChatThread({
  messages,
  proposals,
  bookSlug,
  onApply,
  onDiscard,
  applyBusy,
  applyMessages = {},
}: Props) {
  return (
    <div className="studio-thread">
      {messages.map((m) => (
        <div key={m.id} className={`studio-msg studio-msg--${m.role}`}>
          <div className="studio-msg-bubble">{m.text || (m.streaming ? '…' : '')}</div>
        </div>
      ))}
      {proposals.map((p) => (
        <PatchPreviewCard
          key={p.proposalId}
          proposal={p}
          bookSlug={bookSlug}
          onApply={onApply}
          onDiscard={onDiscard}
          busy={applyBusy}
          applyMessage={applyMessages[p.proposalId]}
        />
      ))}
    </div>
  );
}
