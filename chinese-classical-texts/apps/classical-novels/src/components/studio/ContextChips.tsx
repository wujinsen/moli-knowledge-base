import type { MaintenanceContext } from '../../lib/studio/types';

type Props = {
  context: MaintenanceContext;
  bookSlug: string;
};

export default function ContextChips({ context, bookSlug }: Props) {
  const pageKind = context.page.kind;
  const ingest = context.ingest;

  if (pageKind === 'chapter' && ingest) {
    const missing = ingest.charactersMissingPage?.length ?? 0;
    const bodyOnly = ingest.bodyOnlyCharacters?.length ?? 0;
    return (
      <div className="studio-chips">
        <span className="studio-chip">人物 ×{ingest.charactersListed?.length ?? 0}</span>
        {missing > 0 && <span className="studio-chip studio-chip-warn">缺页 {missing}</span>}
        {bodyOnly > 0 && <span className="studio-chip studio-chip-warn">正文未列 {bodyOnly}</span>}
        {ingest.readUrl && (
          <a className="studio-chip studio-chip-link" href={ingest.readUrl}>
            阅读原文
          </a>
        )}
      </div>
    );
  }

  const items = context.items;
  const keyN = items?.keyItems?.length ?? 0;
  const costumeN = items?.costumes?.length ?? 0;
  const ch = context.chapters?.suggested?.[0];

  return (
    <div className="studio-chips">
      <span className="studio-chip">信物 ×{keyN}</span>
      <span className="studio-chip">服饰 ×{costumeN}</span>
      {ch != null && (
        <a className="studio-chip studio-chip-link" href={`/${bookSlug}/read/zhiben/${ch}`}>
          建议 #{ch} 回
        </a>
      )}
      {(items?.missingFromCrosslinks?.length ?? 0) > 0 && (
        <span className="studio-chip studio-chip-warn">
          crosslinks 缺 {items!.missingFromCrosslinks!.length}
        </span>
      )}
    </div>
  );
}
