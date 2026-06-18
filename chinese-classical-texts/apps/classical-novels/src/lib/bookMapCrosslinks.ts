/** 红楼梦空间地图五图层 · 跨图互链 */

export type MapLayerKey = 'garden' | 'manor' | 'capital' | 'digital-tour' | 'scene';

export interface MapLayerMeta {
  key: MapLayerKey;
  title: string;
  path: string;
}

export const HONGLOU_MAP_LAYERS: MapLayerMeta[] = [
  { key: 'capital', title: '都外与王公', path: '/capital' },
  { key: 'manor', title: '宁荣两府', path: '/manor' },
  { key: 'garden', title: '大观园', path: '/map' },
  { key: 'digital-tour', title: '大观园数字文旅', path: '/digital-tour' },
  { key: 'scene', title: '大观园2.5D', path: '/scene' },
];

/** 桥接节点：多图层共现或叙事接点 */
export const BRIDGE_NODE_REASONS: Record<string, string> = {
  宁荣街: '两府与都外交界',
  家塾: '义学 · 宁荣街侧',
  梨香院: '薛家 · 近东角门入园',
  东角门: '荣府东向入园',
  角门: '园南衔接荣府',
  夹道: '园西衔接荣府',
  大观园: '荣府侧院',
};

/** id → 应互链的图层（不含当前层，由 add 过滤） */
const BRIDGE_NODES: Record<string, MapLayerKey[]> = {
  宁荣街: ['manor', 'capital'],
  家塾: ['manor', 'capital'],
  梨香院: ['manor', 'garden', 'digital-tour', 'scene'],
  东角门: ['manor', 'garden', 'digital-tour'],
  角门: ['manor', 'garden', 'digital-tour'],
  夹道: ['manor', 'garden'],
  大观园: ['manor', 'garden', 'digital-tour', 'scene'],
};

export const BRIDGE_NODE_IDS = Object.keys(BRIDGE_NODE_REASONS);

export function isBridgeNode(id: string): boolean {
  return id in BRIDGE_NODES;
}

export interface RelatedMapLink {
  key: MapLayerKey | 'maps-index';
  label: string;
  href: string;
  reason?: string;
}

export function relatedMapLinks(
  bookSlug: string,
  current: MapLayerKey,
  opts?: { nodeId?: string },
): RelatedMapLink[] {
  const base = `/${bookSlug}`;
  const out: RelatedMapLink[] = [
    { key: 'maps-index', label: '全部空间地图', href: `${base}/maps` },
  ];

  const add = (key: MapLayerKey, reason?: string) => {
    if (key === current) return;
    const layer = HONGLOU_MAP_LAYERS.find((l) => l.key === key);
    if (!layer) return;
    if (out.some((x) => x.key === key)) return;
    out.push({
      key,
      label: layer.title,
      href: `${base}${layer.path}`,
      reason,
    });
  };

  const nodeId = opts?.nodeId;
  const bridgeLayers = nodeId ? BRIDGE_NODES[nodeId] : undefined;

  if (bridgeLayers) {
    const reason = BRIDGE_NODE_REASONS[nodeId!];
    for (const key of bridgeLayers) add(key, reason);
  } else {
    if (current === 'garden' || current === 'digital-tour' || current === 'scene') {
      add('manor', '荣府侧院');
      add('capital', '宁荣街以北');
    }
    if (current === 'manor') {
      add('capital', '宁荣街 / 都外');
      add('garden', '大观园侧院');
      add('digital-tour', 'Archviz 标注');
      add('scene', '可逛全园');
    }
    if (current === 'capital') {
      add('manor', '两府内宅');
      add('garden', '大观园');
      add('digital-tour', '园内鸟瞰');
    }

    if (current === 'digital-tour') add('garden', '逻辑拓扑');
    if (current === 'scene') {
      add('garden', '逻辑拓扑');
      add('digital-tour', 'Archviz 底图');
    }
    if (current === 'garden') {
      add('digital-tour');
      add('scene');
    }
  }

  return out;
}

/** maps 索引页 · 图层嵌套关系（文案用） */
export const MAP_LAYER_NESTING =
  '都外与王公 → 宁荣街 → 宁荣两府 → 大观园（荣府侧院）→ 数字文旅 / 2.5D';

export const MAP_BRIDGE_SUMMARY =
  '桥接节点：宁荣街、家塾（都外↔两府）；梨香院、东角门、角门、夹道（两府↔大观园）';
