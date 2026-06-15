/** 红楼梦空间地图索引（仅 honglou；西游/金瓶梅仍用独立顶栏入口） */

export type BookMapStatus = 'live' | 'planned';

export interface BookMapEntry {
  key: string;
  title: string;
  desc: string;
  href?: string;
  status: BookMapStatus;
  badge?: string;
}

export function bookMapEntries(slug: string, features: string[]): BookMapEntry[] {
  if (slug !== 'honglou') return [];

  const has = (f: string) => features.includes(f);

  return [
    {
      key: 'garden',
      title: '大观园',
      desc: '第17回游线 · 七区 36 节点 · 导览线与回目筛选',
      href: `/${slug}/map`,
      status: has('garden') ? 'live' : 'planned',
      badge: '36 节点',
    },
    {
      key: 'manor',
      title: '宁荣两府',
      desc: '荣宁双中轴 · 门禁层级 · 黛玉入府等导览线',
      href: `/${slug}/manor`,
      status: has('manor') ? 'live' : 'planned',
      badge: '26 节点',
    },
    {
      key: 'scene',
      title: '大观园实景',
      desc: 'Pixi 等距全园 · 坐标同源 2D 地图 · scan 图仅视觉对照',
      href: `/${slug}/scene`,
      status: has('scene') ? 'live' : 'planned',
      badge: '34 节点',
    },
    {
      key: 'capital',
      title: '都外与王公',
      desc: '北静王府、清虚观、铁槛寺等城外节点（规划中）',
      status: 'planned',
    },
  ];
}

export function bookHasLiveMaps(slug: string, features: string[]): boolean {
  return slug === 'honglou' && bookMapEntries(slug, features).some((e) => e.status === 'live');
}
