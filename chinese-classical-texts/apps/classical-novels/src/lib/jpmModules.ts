/** 金瓶梅模块顶栏互链（P6） */

export interface JpmModuleLink {
  feature: string;
  slug: string;
  label: string;
}

export const JPM_MODULE_NAV: JpmModuleLink[] = [
  { feature: 'chain', slug: 'chain', label: '衰败链' },
  { feature: 'silver', slug: 'silver', label: '白银流' },
  { feature: 'town', slug: 'town', label: '市井地图' },
  { feature: 'graph', slug: 'graph', label: '社会网' },
  { feature: 'sna', slug: 'sna', label: 'SNA' },
  { feature: 'bestiary', slug: 'bestiary', label: '图鉴' },
  { feature: 'compare', slug: 'compare', label: '对勘' },
  { feature: 'kaozheng', slug: 'kaozheng', label: '考证' },
];

export function jpmModulesFor(features: string[], current?: string): JpmModuleLink[] {
  return JPM_MODULE_NAV.filter((m) => features.includes(m.feature) && m.slug !== current);
}
