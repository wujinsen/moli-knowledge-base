import type { FinancialData, FinancialTrack } from '../lib/financial';
import { eventHref, silverHref } from '../lib/financial';
import { silverEventHref } from '../lib/chain';

interface Props {
  data: FinancialData;
  bookSlug: string;
}

function TrackLane({ track, bookSlug }: { track: FinancialTrack; bookSlug: string }) {
  return (
    <div className="financial-track mb-8">
      <div className="mb-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="brand text-lg" style={{ color: track.color }}>
          {track.label}
        </h3>
        {track.total_liang != null && track.total_liang > 0 && (
          <span className="chip text-xs">{track.total_liang} 两（节点合计）</span>
        )}
        {track.transaction_count > 0 && (
          <span className="text-xs" style={{ color: 'var(--ink-soft)' }}>
            {track.transaction_count} 笔关联交易
          </span>
        )}
      </div>
      <p className="mb-4 text-sm" style={{ color: 'var(--ink-soft)' }}>
        {track.description}
      </p>
      <div className="flex flex-wrap items-stretch gap-2">
        {track.events.map((ev, i) => (
          <div key={ev.id} className="flex min-w-0 items-center gap-2">
            {i > 0 && (
              <span className="hidden shrink-0 text-lg sm:inline" style={{ color: 'var(--ink-soft)' }}>
                →
              </span>
            )}
            <a
              href={eventHref(bookSlug, ev.id)}
              className="surface block min-w-[140px] max-w-[200px] flex-1 rounded-xl border px-3 py-3 text-sm transition hover:opacity-90"
              style={{ borderColor: track.color }}
            >
              <div className="chip mb-1 text-xs">{ev.financial_kind}</div>
              <div className="font-medium leading-snug" style={{ color: 'var(--ink)' }}>
                {ev.title}
              </div>
              <div className="mt-1 text-xs" style={{ color: 'var(--ink-soft)' }}>
                第{ev.chapter}回
                {ev.amount_liang != null && (
                  <span className="ml-1" style={{ color: 'var(--primary)' }}>
                    · {ev.amount_liang} 两
                  </span>
                )}
              </div>
              {ev.transaction_refs.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {ev.transaction_refs.length > 1 ? (
                    <a
                      href={silverEventHref(bookSlug, ev.id)}
                      className="text-xs hover:underline"
                      style={{ color: 'var(--accent)' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {ev.transaction_refs.length} 笔交易 →
                    </a>
                  ) : (
                    ev.transaction_refs.map((tid) => (
                      <a
                        key={tid}
                        href={silverHref(bookSlug, tid)}
                        className="text-xs hover:underline"
                        style={{ color: 'var(--accent)' }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {tid}
                      </a>
                    ))
                  )}
                </div>
              )}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function FinancialTracks({ data, bookSlug }: Props) {
  return (
    <div className="financial-tracks">
      <p className="mb-6 text-sm leading-relaxed" style={{ color: 'var(--ink-soft)' }}>
        按<strong style={{ color: 'var(--ink)' }}>药铺经营 / 放债帮闲 / 政商贿赂</strong>
        等专题轨分组，与下方全书时间轴互补。数据来自{' '}
        <code className="rounded px-1 text-xs" style={{ background: 'var(--base)' }}>
          build_financial.py
        </code>
        ，与{' '}
        <a href={`/${bookSlug}/silver`} className="hover:underline" style={{ color: 'var(--accent)' }}>
          白银流
        </a>{' '}
        互证。
      </p>
      {data.tracks.map((track) => (
        <TrackLane key={track.id} track={track} bookSlug={bookSlug} />
      ))}
      <p className="text-xs" style={{ color: 'var(--ink-soft)' }}>
        深度阅读：
        <a href={`/${bookSlug}/topics/药铺与放债链`} className="ml-1 hover:underline" style={{ color: 'var(--accent)' }}>
          药铺与放债链 topic
        </a>
      </p>
    </div>
  );
}
