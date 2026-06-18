import { useEffect, useState } from 'react';
import { studioHealth } from '../../lib/studio/client';

export default function StudioApiBanner() {
  const [ok, setOk] = useState<boolean | null>(null);
  const [detail, setDetail] = useState('');

  useEffect(() => {
    studioHealth()
      .then((h) => {
        setOk(h.status === 'ok' && h.novelsRootExists);
        setDetail(h.agentMode ? `agent: ${h.agentMode}` : '');
      })
      .catch((e: Error) => {
        setOk(false);
        setDetail(e.message);
      });
  }, []);

  if (ok === null) return null;
  if (ok) {
    return (
      <div className="studio-banner studio-agent-badge" data-pagefind-ignore>
        Orchestrator 已连接 {detail ? `· ${detail}` : ''}
      </div>
    );
  }

  return (
    <div className="studio-banner studio-banner-warn" data-pagefind-ignore>
      Orchestrator 未连接。终端 A 运行 <code>npm run studio:api</code>，确认{' '}
      <a href="http://127.0.0.1:8787/api/studio/health" target="_blank" rel="noreferrer">
        :8787/health
      </a>{' '}
      返回 ok 后，<strong>重启</strong> <code>npm run dev</code>（需加载 .env.development）。
      {detail ? ` (${detail})` : ''}
    </div>
  );
}
