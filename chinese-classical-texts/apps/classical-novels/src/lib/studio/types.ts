/** 维护台聊天协议 TypeScript 类型（对齐 schemas/studio/*.schema.json v0.1） */

export type BookName = '红楼梦' | '金瓶梅' | '西游记';
export type BookSlug = 'honglou' | 'jinpingmei' | 'xiyouji';

export type PageKind = 'character' | 'item' | 'chapter' | 'topic' | 'location' | 'studio';

export type StudioIntent =
  | 'fix_key_item'
  | 'fix_costume'
  | 'add_plot_bullet'
  | 'query'
  | 'run_guard'
  | 'run_lint'
  | 'ingest_chapter'
  | 'dream_batch'
  | 'topic_fill';

export type ItemIssue =
  | 'missing_wiki_page'
  | 'not_in_item_ids'
  | 'wearer_mismatch'
  | 'wearer_mismatch_ch73'
  | 'missing_from_crosslinks'
  | 'missing_plot_citation';

export interface ItemLink {
  id: string;
  kind?: 'costume' | 'dish' | 'medicine' | 'custom' | 'artifact';
  wikiPath?: string;
  wearer?: string;
  first_appear?: string;
  linked: boolean;
  issues?: ItemIssue[];
}

export interface LintHint {
  code: string;
  severity: 'info' | 'warn' | 'error';
  message: string;
}

export interface MaintenanceContext {
  sessionId: string;
  version: '0.1';
  book: BookName;
  bookSlug: BookSlug;
  rulesRef?: string;
  page: {
    kind: PageKind;
    entityId: string;
    entityType?: string;
    name?: string;
    route: string;
    editionSlug?: string;
  };
  entity: {
    path: string;
    frontmatter: Record<string, unknown>;
    plotBullets?: number;
    relationsCount?: number;
  };
  ingest?: IngestContext;
  items?: {
    keyItems?: ItemLink[];
    costumes?: ItemLink[];
    crosslinksOccupant?: string[];
    missingFromCrosslinks?: string[];
  };
  chapters?: {
    suggested?: number[];
    withItems?: Array<{ n: number; items?: string[]; summary?: string }>;
  };
  lintHints?: LintHint[];
  allowedIntents: StudioIntent[];
}

export interface SourceCitation {
  chapter: number;
  path: string;
  edition?: string;
  excerpt?: string;
  readUrl?: string;
}

export interface FilePatch {
  path: string;
  operation: 'create' | 'update';
  hunkSummary?: string;
  diff: string;
}

export interface PostApply {
  scripts: string[];
  logEntry: string;
  refreshHints?: {
    snapshots?: boolean;
    relations?: boolean;
    bestiary?: boolean;
  };
}

export type ProposalStatus =
  | 'pending'
  | 'applied'
  | 'partially_applied'
  | 'discarded'
  | 'failed';

export interface PatchProposal {
  proposalId: string;
  sessionId: string;
  status: ProposalStatus;
  intent: StudioIntent;
  title: string;
  summary: string;
  sources: SourceCitation[];
  patches: FilePatch[];
  postApply: PostApply;
  guardPreview?: {
    status: 'pass' | 'warn' | 'fail' | 'skipped';
    checked?: number;
    unverified?: Array<{ kind?: string; entityId?: string; reason?: string }>;
  };
  topicFillSuggestion?: {
    path?: string;
    title?: string;
    derived_from?: string[];
    summary?: string;
    bodyMarkdown?: string;
  };
  actions: {
    canApply: boolean;
    canApplyPartial?: boolean;
    canEdit?: boolean;
    canDiscard: boolean;
  };
}

export interface CreateSessionRequest {
  book: BookName;
  bookSlug: BookSlug;
  locale?: string;
  page: {
    kind: PageKind;
    route: string;
    entityId: string;
    entityType?: string;
    editionSlug?: string;
  };
  viewer?: { role: 'maintainer' | 'reader' };
}

export interface IngestTask {
  id: string;
  label: string;
  severity: 'info' | 'warn' | 'error';
  entities?: string[];
}

export interface IngestContext {
  chapter: number;
  title?: string;
  edition?: string;
  editionSlug?: string;
  readUrl?: string;
  excerpt?: string;
  charactersListed?: string[];
  charactersMissingPage?: string[];
  bodyOnlyCharacters?: string[];
  locationsMissingPage?: string[];
  itemsMissingPage?: string[];
  tasks?: IngestTask[];
}

export interface IngestReport extends IngestContext {
  book: BookName;
  bookSlug: BookSlug;
  chapterPath: string;
  generatedAt: string;
  ready?: boolean;
  frontmatter: {
    characters: number;
    locations: number;
    items: number;
    hasSummary: boolean;
  };
  charactersWithPage?: string[];
  locationsListed?: string[];
  itemsListed?: string[];
}

export interface SendMessageRequest {
  text: string;
  clientMessageId?: string;
  intentHint?: {
    type: StudioIntent;
    params?: Record<string, unknown>;
  };
}

export type StudioSSEEvent =
  | { event: 'message.delta'; data: { text: string } }
  | { event: 'message.done'; data: { messageId: string; role: 'assistant' | 'user' } }
  | { event: 'tool.start'; data: { tool: string; args: Record<string, unknown> } }
  | { event: 'tool.done'; data: { tool: string; summary: string } }
  | { event: 'proposal.ready'; data: PatchProposal }
  | { event: 'guard.result'; data: PatchProposal['guardPreview'] }
  | { event: 'error'; data: { code: string; message: string } };

export interface ApplyProposalRequest {
  patchPaths?: string[];
  skipPostApply?: boolean;
}

export interface ApplyProposalResponse {
  jobId: string;
  status: string;
  appliedPaths: string[];
  logAppended?: boolean;
  message?: string;
  dryRun?: boolean;
  postApply?: {
    ok?: boolean;
    skipped?: boolean;
    error?: string;
    scripts?: Array<{
      command: string;
      returncode: number;
      stdoutTail?: string;
      stderrTail?: string;
    }>;
  };
  refreshHints?: PostApply['refreshHints'];
}

export interface LintSection {
  id: string;
  title: string;
  count: number;
  items: string[];
  truncated?: number;
}

export interface DensityCharacterRow {
  id: string;
  score: number;
  rel: number;
  plot: number;
  inbound: number;
  flags: string[];
}

export interface LintDensityReport {
  totalCharacters: number;
  graphNodes: number;
  graphEdges: number;
  scoreDistribution: Record<string, number>;
  priorityBatch: DensityCharacterRow[];
  structMissing: Array<{ id: string; missing: string[] }>;
  structMissingTotal: number;
  weakInbound: Array<{ id: string; inbound: number }>;
  weakInboundTotal: number;
  missingRelTargets: string[];
  oneWayRels: string[];
  oneWayRelsTotal: number;
}

export interface LintReport {
  book: string;
  bookSlug: BookSlug;
  generatedAt: string;
  totalIssues: number;
  passed: boolean;
  sections: LintSection[];
  density: LintDensityReport;
}

export interface GraphEdgeTypeRow {
  type: string;
  count: number;
}

export interface GraphReport {
  book: string;
  bookSlug: BookSlug;
  generatedAt: string;
  preview: boolean;
  applied: boolean;
  nodeCount: number;
  edgeCount: number;
  characterCount: number;
  topicCount: number;
  contradictionEdges: number;
  edgeTypes: GraphEdgeTypeRow[];
  warningCount: number;
  warnings: string[];
  truncatedWarnings?: number;
  outputPath: string;
  snaPath?: string | null;
  snaHubs?: string[];
  error?: string;
}

export interface DreamTierCatalogEntry {
  id: string;
  label: string;
  thinLabel: string;
  goal: string;
  candidateCount: number;
  script: string;
  postApply: string[];
}

export interface DreamCatalog {
  book?: string;
  bookSlug: BookSlug;
  supported?: boolean;
  message?: string;
  generatedAt: string;
  scoreDistribution?: Record<string, number>;
  totalCharacters?: number;
  weakInboundTotal?: number;
  tiers: DreamTierCatalogEntry[];
  recommendedTierId?: string | null;
}

export interface DreamChangeRow {
  summary: string;
  characterId?: string | null;
}

export interface DreamStuckRow {
  id: string;
  score: number;
  rel: number;
  plot: number;
  inbound: number;
}

export interface DreamTierPreview {
  book: string;
  bookSlug: BookSlug;
  tierId: string;
  label: string;
  thinLabel: string;
  goal: string;
  preview: boolean;
  applied: boolean;
  candidateCount: number;
  patchCount: number;
  stuckCount: number;
  changes: DreamChangeRow[];
  truncatedChanges?: number;
  stuck: DreamStuckRow[];
  truncatedStuck?: number;
  postApply: string[];
  postApplyResults?: Array<{
    command: string;
    returncode: number;
    stdoutTail?: string;
    stderrTail?: string;
  }>;
  stdoutTail?: string;
  generatedAt: string;
}

export type DreamProgressStage = 'preview' | 'patch' | 'postApply' | 'refresh';

export interface DreamProgressEvent {
  event: 'stage' | 'line' | 'milestone' | 'log';
  stage?: DreamProgressStage;
  label?: string;
  step?: number;
  total?: number;
  command?: string;
  index?: number;
  text?: string;
  characterId?: string | null;
  patchCount?: number;
}

export interface GuardIssueItem {
  kind: 'first_appear' | 'plot' | 'relation' | 'transaction';
  characterId?: string;
  entityId?: string;
  severity: 'unverified' | 'warn';
  message: string;
  chapter?: number;
  chapters?: number[];
  hint?: string;
  target?: string;
  relationType?: string;
}

export interface GuardSection {
  id: string;
  title: string;
  count: number;
  checked?: number;
  items: GuardIssueItem[];
  truncated?: number;
}

export interface GuardSummary {
  firstAppearUnverified: number;
  plotChecked: number;
  plotUnverified: number;
  relationChecked: number;
  relationUnverified: number;
  transactionIssues: number;
}

export interface GuardReport {
  book: string;
  bookSlug: BookSlug;
  generatedAt: string;
  passed: boolean;
  totalIssues: number;
  summary: GuardSummary;
  sections: GuardSection[];
}

export interface StudioTodo {
  id: string;
  kind: StudioIntent;
  message: string;
  suggestedPrompt: string;
  severity: 'info' | 'warn' | 'error';
  entityId?: string;
  chapter?: number;
  editionSlug?: string;
  readUrl?: string;
}

export interface StudioTodosReport {
  book: BookName;
  bookSlug: BookSlug;
  generatedAt: string;
  totalTodos: number;
  todos: StudioTodo[];
  sources?: {
    crosslinks?: number;
    ingest?: number;
    density?: number;
  };
}
