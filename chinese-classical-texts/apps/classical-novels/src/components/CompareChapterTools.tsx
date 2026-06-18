import { useCallback, useEffect, useRef, useState } from 'react';
import type { CompareVariantRow } from '../lib/compareIndex';

interface Props {
  bookSlug: string;
  pairSlug: string;
  chapter: number;
  pairLabel: string;
  leftLabel: string;
  rightLabel: string;
  variants: CompareVariantRow[];
  features: string[];
}

function highlightText(container: HTMLElement, needle: string, side: 'a' | 'b', variantId: string): boolean {
  if (!needle || needle.length < 2) return false;
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  let node: Text | null;
  while ((node = walker.nextNode() as Text | null)) {
    const idx = node.textContent?.indexOf(needle) ?? -1;
    if (idx < 0) continue;
    const range = document.createRange();
    range.setStart(node, idx);
    range.setEnd(node, idx + needle.length);
    const mark = document.createElement('mark');
    mark.className = `compare-highlight compare-highlight--${side}`;
    mark.dataset.variantId = variantId;
    mark.dataset.compareSide = side;
    try {
      range.surroundContents(mark);
      return true;
    } catch {
      continue;
    }
  }
  return false;
}

function scrollToVariant(variantId: string) {
  const marks = document.querySelectorAll(`mark[data-variant-id="${variantId}"]`);
  if (marks.length === 0) return;
  marks.forEach((m) => m.classList.add('compare-highlight--active'));
  marks[0]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

export default function CompareChapterTools({
  bookSlug,
  chapter,
  pairLabel,
  leftLabel,
  rightLabel,
  variants,
  features,
}: Props) {
  const [focusId, setFocusId] = useState<string | null>(null);
  const synced = useRef(false);

  const applyHighlights = useCallback(() => {
    const root = document.querySelector('[data-edition-compare]');
    if (!root) return;
    const left = root.querySelector('[data-compare-scroll="left"]') as HTMLElement | null;
    const right = root.querySelector('[data-compare-scroll="right"]') as HTMLElement | null;
    if (!left || !right) return;

    root.querySelectorAll('mark.compare-highlight').forEach((m) => {
      const parent = m.parentNode;
      if (!parent) return;
      parent.replaceChild(document.createTextNode(m.textContent ?? ''), m);
      parent.normalize();
    });

    for (const v of variants) {
      if (v.text_a) highlightText(left, v.text_a, 'a', v.id);
      if (v.text_b) highlightText(right, v.text_b, 'b', v.id);
    }
  }, [variants]);

  useEffect(() => {
    applyHighlights();
    const url = new URL(window.location.href);
    const vid = url.searchParams.get('variant');
    if (vid && variants.some((v) => v.id === vid)) {
      setFocusId(vid);
      requestAnimationFrame(() => scrollToVariant(vid));
    }
  }, [applyHighlights, variants]);

  useEffect(() => {
    if (!focusId) return;
    document.querySelectorAll('mark.compare-highlight--active').forEach((m) => {
      m.classList.remove('compare-highlight--active');
    });
    scrollToVariant(focusId);
    const url = new URL(window.location.href);
    url.searchParams.set('variant', focusId);
    window.history.replaceState({}, '', url.toString());
  }, [focusId]);

  useEffect(() => {
    const root = document.querySelector('[data-edition-compare]');
    if (!root || synced.current) return;
    const left = root.querySelector('[data-compare-scroll="left"]');
    const right = root.querySelector('[data-compare-scroll="right"]');
    if (!left || !right) return;
    synced.current = true;
    let locking = false;
    const sync = (src: Element, dst: Element) => {
      if (locking) return;
      locking = true;
      const el = src as HTMLElement;
      const peer = dst as HTMLElement;
      const ratio = el.scrollTop / Math.max(1, el.scrollHeight - el.clientHeight);
      peer.scrollTop = ratio * Math.max(0, peer.scrollHeight - peer.clientHeight);
      locking = false;
    };
    left.addEventListener('scroll', () => sync(left, right), { passive: true });
    right.addEventListener('scroll', () => sync(right, left), { passive: true });
  }, []);

  return (
    <div className="compare-chapter-tools mb-4 space-y-4">
      {variants.length > 0 && (
        <section className="surface px-4 py-4 sm:px-6">
          <h2 className="section-title mb-2 text-sm">
            本回异文锚点（{variants.length}）· {pairLabel}
          </h2>
          <ul className="space-y-2 text-sm text-muted">
            {variants.map((v) => (
              <li
                key={v.id}
                className="cursor-pointer border-l-2 pl-3 transition hover:opacity-100"
                style={{
                  borderColor: focusId === v.id ? 'var(--accent)' : 'color-mix(in srgb, var(--accent) 40%, transparent)',
                  opacity: focusId && focusId !== v.id ? 0.65 : 1,
                }}
                onClick={() => setFocusId(v.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setFocusId(v.id);
                  }
                }}
                role="button"
                tabIndex={0}
              >
                <span className="chip mr-1 text-xs">{v.category}</span>
                {v.summary}
                {v.text_a && v.text_b && (
                  <div className="mt-1 text-xs opacity-90">
                    <span className="compare-chip-left">{leftLabel}</span>「{v.text_a}」
                    <span className="mx-1">↔</span>
                    <span className="compare-chip-right">{rightLabel}</span>「{v.text_b}」
                  </div>
                )}
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {v.topic_id && features.includes('graph') && (
                    <a
                      href={`/${bookSlug}/graph?focus=${encodeURIComponent(v.topic_id)}`}
                      className="text-xs hover:underline"
                      style={{ color: 'var(--accent)' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      图谱议题 →
                    </a>
                  )}
                  {v.tags.includes('白银流') && features.includes('silver') && (
                    <a
                      href={`/${bookSlug}/silver?chapter=${chapter}`}
                      className="text-xs hover:underline"
                      style={{ color: 'var(--accent)' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      白银流 →
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex flex-wrap gap-2 text-xs text-muted">
        <span>J3：双栏同步滚动 · 异文高亮 · 点击锚点定位</span>
        {bookSlug === 'jinpingmei' && (
          <a href={`/${bookSlug}/topics/版本对勘样本`} className="hover:underline" style={{ color: 'var(--accent)' }}>
            版本对勘样本 →
          </a>
        )}
      </div>
    </div>
  );
}
