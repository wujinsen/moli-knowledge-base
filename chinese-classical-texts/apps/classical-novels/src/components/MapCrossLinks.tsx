import { relatedMapLinks, type MapLayerKey } from '../lib/bookMapCrosslinks';

interface Props {
  bookSlug: string;
  current: MapLayerKey;
  nodeId?: string;
  size?: 'sm' | 'xs';
  className?: string;
}

export default function MapCrossLinks({
  bookSlug,
  current,
  nodeId,
  size = 'xs',
  className = '',
}: Props) {
  const links = relatedMapLinks(bookSlug, current, { nodeId });
  const text = size === 'sm' ? 'text-sm' : 'text-xs';

  return (
    <nav className={`flex flex-col gap-1.5 ${className}`} aria-label="相关空间地图">
      {links.map((link) => (
        <a
          key={link.key}
          href={link.href}
          className={`${text} text-slate-500 hover:text-slate-300`}
          title={link.reason}
        >
          {link.label} →
        </a>
      ))}
    </nav>
  );
}
