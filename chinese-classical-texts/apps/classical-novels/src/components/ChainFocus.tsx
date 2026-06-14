import { useEffect } from 'react';

interface Props {
  /** 初始 focus（构建期 ?focus= 查询参数） */
  initialFocus?: string;
}

function scrollToFocus(focus: string) {
  const id = focus.startsWith('chain-') ? focus : `chain-${focus}`;
  const el = document.getElementById(id);
  if (!el) return;
  document.querySelectorAll('[data-chain-focus="true"]').forEach((n) => {
    n.removeAttribute('data-chain-focus');
  });
  el.setAttribute('data-chain-focus', 'true');
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

export default function ChainFocus({ initialFocus }: Props) {
  useEffect(() => {
    const fromUrl = () => {
      const params = new URLSearchParams(window.location.search);
      const q = params.get('focus');
      const hash = window.location.hash.replace(/^#chain-/, '').replace(/^#/, '');
      const focus = q || hash || initialFocus;
      if (focus) scrollToFocus(focus);
    };
    fromUrl();
    window.addEventListener('hashchange', fromUrl);
    window.addEventListener('popstate', fromUrl);
    return () => {
      window.removeEventListener('hashchange', fromUrl);
      window.removeEventListener('popstate', fromUrl);
    };
  }, [initialFocus]);

  return (
    <style>{`
      [data-chain-focus="true"] {
        outline: 2px solid color-mix(in srgb, var(--accent) 55%, transparent);
        outline-offset: 2px;
        background: color-mix(in srgb, var(--accent) 6%, var(--surface));
      }
    `}</style>
  );
}
