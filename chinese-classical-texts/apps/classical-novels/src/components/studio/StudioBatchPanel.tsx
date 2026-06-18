import { useState } from 'react';
import type { BookSlug } from '../../lib/studio/types';
import DreamDashboard from './DreamDashboard';
import GraphDashboard from './GraphDashboard';
import GuardDashboard from './GuardDashboard';
import LintDashboard from './LintDashboard';

type BatchTab = 'lint' | 'dream' | 'graph' | 'guard';

type Props = {
  bookSlug: BookSlug;
  onOpenEntity?: (entityId: string) => void;
};

export default function StudioBatchPanel({ bookSlug, onOpenEntity }: Props) {
  const [tab, setTab] = useState<BatchTab>('lint');

  return (
    <div className="studio-batch-panel">
      <div className="studio-batch-tabs" role="tablist" aria-label="批处理命令">
        {(['lint', 'dream', 'graph', 'guard'] as const).map((key) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={tab === key}
            className={tab === key ? 'studio-batch-tab studio-batch-tab-active' : 'studio-batch-tab'}
            onClick={() => setTab(key)}
          >
            /{key}
          </button>
        ))}
      </div>

      {tab === 'lint' && <LintDashboard bookSlug={bookSlug} onOpenEntity={onOpenEntity} />}
      {tab === 'dream' && <DreamDashboard bookSlug={bookSlug} onOpenEntity={onOpenEntity} />}
      {tab === 'graph' && <GraphDashboard bookSlug={bookSlug} />}
      {tab === 'guard' && <GuardDashboard bookSlug={bookSlug} onOpenEntity={onOpenEntity} />}
    </div>
  );
}
