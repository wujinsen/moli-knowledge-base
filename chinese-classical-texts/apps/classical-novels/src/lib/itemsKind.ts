/** 名物类别：纯函数 / 常量，不依赖 astro:content，可安全用于客户端组件。 */

export type ItemKind = 'medicine' | 'dish' | 'costume' | 'custom' | 'artifact';

const KIND_LABEL: Record<ItemKind, string> = {
  medicine: '医药',
  dish: '饮食',
  costume: '服饰',
  custom: '民俗',
  artifact: '法宝',
};

export function kindLabel(kind: ItemKind): string {
  return KIND_LABEL[kind];
}

export function itemsIndexTitle(book: string): string {
  return book === '西游记' ? '法宝谱系' : '名物百科';
}
