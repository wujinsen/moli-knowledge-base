import honglou from '../data/红楼梦.relations.json';
import jinpingmei from '../data/金瓶梅.relations.json';
import xiyouji from '../data/西游记.relations.json';

export interface RelationNode {
  id: string;
  type: string;
  faction: string;
  weight?: number;
  chapter?: number;
  summary?: string;
  variantIds?: string[];
}

export interface RelationEdge {
  source: string;
  target: string;
  type: string;
  contradiction?: boolean;
  inference?: boolean;
}

export interface RelationGraphData {
  nodes: RelationNode[];
  edges: RelationEdge[];
}

const BY_SLUG: Record<string, RelationGraphData> = {
  honglou,
  xiyouji,
  jinpingmei,
};

/** 按书目 slug 加载关系图谱 JSON（构建时静态 import，不依赖 content store） */
export function relationGraphForSlug(slug: string): RelationGraphData {
  return BY_SLUG[slug] ?? { nodes: [], edges: [] };
}
