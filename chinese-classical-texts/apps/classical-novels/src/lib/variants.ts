import { getCollection } from 'astro:content';

export async function variantsForChapter(book: string, chapter: number) {
  const all = await getCollection('variants');
  return all
    .filter((v) => v.data.book === book && v.data.chapter === chapter)
    .sort((a, b) => a.data.category.localeCompare(b.data.category, 'zh'));
}

export async function chaptersWithVariants(book: string): Promise<Set<number>> {
  const all = await getCollection('variants');
  const set = new Set<number>();
  for (const v of all) {
    if (v.data.book === book) set.add(v.data.chapter);
  }
  return set;
}

export async function variantCountByChapter(book: string): Promise<Map<number, number>> {
  const all = await getCollection('variants');
  const map = new Map<number, number>();
  for (const v of all) {
    if (v.data.book !== book) continue;
    map.set(v.data.chapter, (map.get(v.data.chapter) ?? 0) + 1);
  }
  return map;
}
