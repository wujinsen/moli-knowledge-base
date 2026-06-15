/** 取经路线：仅保留需独立插画的地标（其余节点用圆/菱形） */
export const CUSTOM_ROUTE_ICONS: Record<string, string> = {
  火焰山: 'huoyanshan.png',
};

export function hasCustomRouteIcon(nodeId: string): boolean {
  return nodeId in CUSTOM_ROUTE_ICONS;
}

/** public 目录下图标 URL 路径（含 BASE_URL） */
export function routeIconPublicPath(bookSlug: string, file: string): string {
  const base = (import.meta.env.BASE_URL ?? '/').replace(/\/$/, '');
  const path = `${base}/${bookSlug}/route/icons/${file}`.replace(/\/+/g, '/');
  return path.startsWith('/') ? path : `/${path}`;
}

/** 浏览器内绝对 URL，供预加载与 ECharts */
export function routeIconAbsoluteUrl(bookSlug: string, file: string): string {
  const path = routeIconPublicPath(bookSlug, file);
  const bust = file.endsWith('.png') ? `?v=${file === 'huoyanshan.png' ? 3 : 2}` : '';
  if (typeof window === 'undefined') return `${path}${bust}`;
  return `${window.location.origin}${path}${bust}`;
}

/** ECharts graph `image://` 符号（须用绝对 URL，否则 PNG 常加载失败） */
export function routeIconSymbol(bookSlug: string, nodeId: string): string | null {
  const file = CUSTOM_ROUTE_ICONS[nodeId];
  if (!file) return null;
  return `image://${routeIconAbsoluteUrl(bookSlug, file)}`;
}

/** 预加载自定义 PNG，避免 ECharts 首次渲染用占位圆 */
export function preloadRouteIcons(bookSlug: string): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve();
  const pngs = Object.values(CUSTOM_ROUTE_ICONS).filter((f) => f.endsWith('.png'));
  if (pngs.length === 0) return Promise.resolve();
  return Promise.all(
    pngs.map(
      (file) =>
        new Promise<void>((resolve) => {
          const img = new Image();
          img.onload = () => resolve();
          img.onerror = () => resolve();
          img.src = routeIconAbsoluteUrl(bookSlug, file);
        }),
    ),
  ).then(() => undefined);
}

export function routeIconSize(selected: boolean): [number, number] {
  const base = 64;
  const s = selected ? base * 1.28 : base;
  return [s, s];
}

export function routeIconGlow(nodeId: string): string {
  if (nodeId === '火焰山') return '#ff8c42';
  return '#ff8c42';
}
