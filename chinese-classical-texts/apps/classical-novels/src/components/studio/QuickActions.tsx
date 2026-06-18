import type { StudioIntent } from '../../lib/studio/types';

type Props = {
  disabled?: boolean;
  mode?: 'character' | 'chapter';
  onAction: (intent: StudioIntent, label: string) => void;
};

const CHARACTER_ACTIONS: { intent: StudioIntent; label: string; prompt: string }[] = [
  { intent: 'fix_key_item', label: '补信物', prompt: '补全信物链与 crosslinks' },
  { intent: 'fix_costume', label: '改服饰', prompt: '更正服饰字段与名物页' },
  { intent: 'run_lint', label: '体检', prompt: 'run lint' },
];

const CHAPTER_ACTIONS: { intent: StudioIntent; label: string; prompt: string }[] = [
  {
    intent: 'ingest_chapter',
    label: '摄取本回',
    prompt: '摄取本回：补 frontmatter 人物、更新登场者关键情节（原文 body 只读）',
  },
  { intent: 'run_guard', label: '校验', prompt: 'run guard on touched entities' },
];

export default function QuickActions({ disabled, mode = 'character', onAction }: Props) {
  const actions = mode === 'chapter' ? CHAPTER_ACTIONS : CHARACTER_ACTIONS;
  return (
    <div className="studio-quick">
      {actions.map((a) => (
        <button
          key={a.intent}
          type="button"
          className="studio-quick-btn"
          disabled={disabled}
          onClick={() => onAction(a.intent, a.prompt)}
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}
