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
      key: 'digital-tour',
      title: '大观园数字文旅',
      desc: 'Archviz 鸟瞰底图 + 36 处 wiki 坐标标注 · 导览线 / 分区筛选 / 词条联动',
      href: `/${slug}/digital-tour`,
      status: has('garden') ? 'live' : 'planned',
      badge: '数字文旅',
    },
    {
      key: 'scene',
      title: '大观园2.5D',
      desc: 'Pixi 等距全园 · 坐标同源 2D 地图 · 可逛可点 NPC',
      href: `/${slug}/scene`,
      status: has('scene') ? 'live' : 'planned',
      badge: '2.5D',
    },
    {
      key: 'capital',
      title: '都外与王公',
      desc: '王府侯伯 · 清虚观/铁槛寺 · 路祭/打醮/封妃导览',
      href: `/${slug}/capital`,
      status: has('capital') ? 'live' : 'planned',
      badge: '26 节点',
    },
  ];
}

export function bookHasLiveMaps(slug: string, features: string[]): boolean {
  return slug === 'honglou' && bookMapEntries(slug, features).some((e) => e.status === 'live');
}
