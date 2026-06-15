/** 诗词意象 / 互文网络（纯函数，不含 astro:content） */

export type ImageryPhase = '欲起' | '聚敛' | '极盛' | '反噬' | '散尽';
export type ImageryTemperature = '冷' | '热';

export interface ImageryLink {
  target: string;
  target_kind: 'character' | 'imagery';
  predicate: string;
  inference: boolean;
  chapter?: number;
  note?: string;
  phase?: ImageryPhase;
  temperature?: ImageryTemperature;
}

export type ImageryLayer = '太虚' | '人间';

export interface ImageryData {
  id: string;
  subtype: string;
  title: string;
  text?: string;
  layer?: ImageryLayer;
  chapters: number[];
  characters: string[];
  links: ImageryLink[];
  summary?: string;
}

export type ImageryEntry = { data: ImageryData };

export type ImageryNodeKind =
  | 'character'
  | 'judgment'
  | 'poem'
  | 'symbol'
  | 'flower_lot'
  | 'myth'
  | 'name_omen'
  | 'object_omen'
  | 'tune_omen'
  | 'alchemy'
  | 'place_omen';

export interface ImageryGraphNode {
  id: string;
  label: string;
  kind: ImageryNodeKind;
  size: number;
  layer?: ImageryLayer;
}

/** 跨层映射边（太虚↔人间）：投胎历劫 / 还泪 / 投影 / 归空 */
export const MAPPING_PREDICATES = new Set(['还泪', '历劫', '投影', '归彼大荒']);
/** 影身边：丫鬟为主子之影（晴雯→黛玉、袭人→宝钗） */
export const SHADOW_PREDICATES = new Set(['影身']);

export interface ImageryGraphEdge {
  source: string;
  target: string;
  predicate: string;
  inference: boolean;
  chapter?: number;
  note?: string;
  phase?: ImageryPhase;
  temperature?: ImageryTemperature;
}

export interface ImageryGraph {
  nodes: ImageryGraphNode[];
  edges: ImageryGraphEdge[];
}

export const SUBTYPE_LABEL: Record<string, string> = {
  myth: '神话本源',
  judgment: '判词',
  poem: '诗词',
  symbol: '象征',
  flower_lot: '花签',
  name_omen: '名字谶',
  object_omen: '物象谶',
  tune_omen: '曲牌宝卷',
  alchemy: '丹道意象',
  place_omen: '地名隐喻',
  character: '人物',
};

/** 示例链路（按书 slug 区分；图谱按 bookSlug 取对应链路） */
export const HIGHLIGHT_CHAINS: Record<string, { name: string; path: string[] }[]> = {
  honglou: [
    { name: '木石前盟：绛珠→黛玉', path: ['hl-myth-jiangzhu', '林黛玉', 'hl-s-zhu'] },
    { name: '顽石历劫→宝玉', path: ['hl-myth-stone', '贾宝玉', 'hl-s-yu'] },
    { name: '太虚→判词→黛玉', path: ['hl-myth-taixu', 'hl-j-01', '林黛玉'] },
    { name: '影身：晴雯→黛玉', path: ['晴雯', 'hl-s-furong', '林黛玉'] },
    { name: '影身：袭人→宝钗', path: ['袭人', '薛宝钗', 'hl-s-jin'] },
    { name: '金玉—钗黛', path: ['hl-s-yu', '贾宝玉', 'hl-s-jin', '薛宝钗'] },
    { name: '迎春—中山狼', path: ['hl-j-07', 'hl-p-19', '孙绍祖', '贾迎春'] },
  ],
  jinpingmei: [
    { name: '总纲：酒色财气→西门庆', path: ['jpm-tune-jiusecaiqi', '西门庆'] },
    { name: '聚敛：瓶→瓶儿→西门府', path: ['jpm-name-pinger', '李瓶儿', '西门庆'] },
    { name: '转折：雪狮子→瓶儿崩塌', path: ['jpm-obj-xueshizi', '李瓶儿', '西门庆'] },
    { name: '反噬：胡僧药→西门庆暴亡', path: ['jpm-obj-husengyao', '西门庆'] },
    { name: '散尽：陈经济败家', path: ['jpm-name-chenjingji', '陈经济', '西门庆'] },
  ],
  xiyouji: [
    { name: '心猿→悟空（金）', path: ['xyj-dan-xinyuan', '孙悟空'] },
    { name: '意马→龙马', path: ['xyj-dan-yima', '白龙马'] },
    { name: '金木相克：心猿—木母', path: ['xyj-dan-xinyuan', 'xyj-dan-mumu', '猪八戒'] },
    { name: '黄婆调和金木', path: ['xyj-dan-huangpo', 'xyj-dan-xinyuan', 'xyj-dan-mumu'] },
    { name: '水火相济：心猿—意马', path: ['xyj-dan-xinyuan', 'xyj-dan-yima', '白龙马'] },
    { name: '婴儿火性：火焰山—红孩儿', path: ['xyj-place-huoyanshan', 'xyj-dan-yinger', '红孩儿'] },
    { name: '修心起点：灵台方寸山', path: ['xyj-place-lingtai', '孙悟空'] },
  ],
};

const NODE_SIZE: Record<string, number> = {
  character: 28,
  myth: 30,
  judgment: 22,
  poem: 20,
  symbol: 24,
  flower_lot: 20,
  name_omen: 24,
  object_omen: 24,
  tune_omen: 22,
  alchemy: 28,
  place_omen: 24,
};

function nodeKind(subtype: string | 'character'): ImageryGraphNode['kind'] {
  if (subtype === 'character') return 'character';
  return subtype as ImageryGraphNode['kind'];
}

function resolveTargetId(target: string, targetKind: string): string {
  return targetKind === 'imagery' ? target : target;
}

/** 从 imagery 实体 + 额外 JSON 边构建互文图 */
export function buildImageryGraph(
  items: ImageryEntry[],
  extraLinks: ImageryGraphEdge[] = [],
): ImageryGraph {
  const nodeMap = new Map<string, ImageryGraphNode>();
  const edges: ImageryGraphEdge[] = [...extraLinks];
  const edgeKeys = new Set(extraLinks.map((e) => `${e.source}|${e.predicate}|${e.target}`));

  const addNode = (
    id: string,
    label: string,
    kind: ImageryGraphNode['kind'],
    layer?: ImageryLayer,
  ) => {
    const existing = nodeMap.get(id);
    if (!existing) {
      nodeMap.set(id, { id, label, kind, size: NODE_SIZE[kind] ?? 20, layer });
    } else if (layer && !existing.layer) {
      existing.layer = layer;
    }
  };

  for (const item of items) {
    const d = item.data;
    addNode(d.id, d.title, nodeKind(d.subtype), d.layer);
    for (const c of d.characters) {
      addNode(c, c, 'character', d.layer === '太虚' ? undefined : '人间');
    }
    for (const link of d.links) {
      const tid = resolveTargetId(link.target, link.target_kind);
      const tlabel = link.target_kind === 'imagery' ? link.target : link.target;
      addNode(tid, tlabel, link.target_kind === 'imagery' ? nodeKind('symbol') : 'character');
      const edge: ImageryGraphEdge = {
        source: d.id,
        target: tid,
        predicate: link.predicate,
        inference: link.inference,
        chapter: link.chapter,
        note: link.note,
        phase: link.phase,
        temperature: link.temperature,
      };
      const key = `${edge.source}|${edge.predicate}|${edge.target}`;
      if (!edgeKeys.has(key)) {
        edges.push(edge);
        edgeKeys.add(key);
      }
    }
  }

  for (const e of extraLinks) {
    addNode(e.source, e.source.startsWith('hl-') ? e.source : e.source, e.source.startsWith('hl-') ? 'symbol' : 'character');
    addNode(e.target, e.target, e.target.startsWith('hl-') ? 'symbol' : 'character');
  }

  // 修正 extra link 节点 label：用 items 里的 title
  for (const item of items) {
    const n = nodeMap.get(item.data.id);
    if (n) n.label = item.data.title;
  }

  return { nodes: [...nodeMap.values()], edges };
}

export function sortImagery(items: ImageryEntry[]): ImageryEntry[] {
  const order = [
    'myth', 'judgment', 'poem', 'symbol', 'flower_lot',
    'tune_omen', 'name_omen', 'object_omen',
    'alchemy', 'place_omen',
  ];
  return [...items].sort((a, b) => {
    const ia = order.indexOf(a.data.subtype);
    const ib = order.indexOf(b.data.subtype);
    if (ia !== ib) return ia - ib;
    return a.data.title.localeCompare(b.data.title, 'zh');
  });
}

export function subtypeLabel(subtype: string): string {
  return SUBTYPE_LABEL[subtype] ?? subtype;
}

export function chapterLabel(chapters: number[]): string {
  if (chapters.length === 0) return '—';
  if (chapters.length === 1) return `第${chapters[0]}回`;
  return `第${chapters[0]}–${chapters[chapters.length - 1]}回`;
}
