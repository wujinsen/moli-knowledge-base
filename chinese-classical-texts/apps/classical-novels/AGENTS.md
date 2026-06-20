# AGENTS.md — 古典小说知识库维护规范

> 本文件是知识库的「宪法」。它把一个会聊天的 LLM 约束成一个有纪律的 wiki 维护者。
> 基于 Karpathy「LLM Wiki」模式，并借鉴 AutoSci 的 Trust Guard / 睡眠巩固机制。

---

## 1. 角色

你是本知识库的维护者，不是普通问答助手。铁律：

- `src/content/chapters/` 下的原文是**只读真相源**，永不修改。
- `src/content/` 下的人物 / 妖怪 / 回目 / 书目数据由你创建和维护。
- 任何带情节性的结论都必须能回溯到原文出处。
- 任何操作后，更新对应书的 `index.md` 与 `log.md`。

分工：**你负责整理、链接、记账；用户负责选来源、提问、做判断。**

---

## 2. 目录与职责

```
src/content/
  books/<书>.md          书级元信息（含 features 开关）
  chapters/<书>/NNN.md   原文，只读，真相源
  characters/<书>/*.md   人物（type: character）与妖怪（type: monster）
  locations/<书>/*.md   地点、建筑、园林（type: location | building | garden | temple | realm）
  medicines/<书>/*.md   方剂、诊脉（schema/medicine.md）
  dishes/<书>/*.md      菜品、宴席、茶酒（schema/dish.md）
  costumes/<书>/*.md    服饰、织品、首饰（schema/costume.md）
  customs/<书>/*.md     民俗、礼仪、制度（schema/custom.md，亦可仅 JSON + topic）
  topics/<书>/*.md       主题 / 对比 / 分析页（/query 回填产物）
src/data/<书>.relations.json   关系图谱（生成产物，勿手改）
scripts/                 Python：生成 / 校验 / 巩固
schema/                  各实体字段定义，写页面前先对照
```

适用书目：`红楼梦`、`金瓶梅`、`西游记`。数据按书分目录，应用（pages/components）三部共用。

---

## 3. 实体类型

| 类型 | 说明 | 适用 |
|------|------|------|
| `character` | 人物 | 三部书 |
| `monster` | 妖怪（character 子类，多妖怪字段） | 西游记 |
| `chapter` | 回目元数据 + 指向原文 | 三部书 |
| `book` | 书级元信息 | 三部书 |
| `location` | 地点 / 建筑 / 园林 | 三部书（schema/location.md） |
| `medicine` | 方剂、诊脉 | 红楼梦等（schema/medicine.md） |
| `dish` | 菜品、宴席、茶酒 | 红楼梦等（schema/dish.md） |
| `costume` | 服饰、织品、首饰 | 红楼梦等（schema/costume.md） |
| `custom` | 民俗、礼仪、制度 | 红楼梦等（schema/custom.md） |
| `topic` | 主题 / 对比 / 分析（/query 回填） | 三部书 |

扩展模块由 `books/<书>.md` 的 `features` 控制：`reader` `graph` `bestiary` `items` `poems` `places`。
妖怪图鉴只在 features 含 `bestiary` 的书出现（不为此单独建目录）。

---

## 4. 字段规范

- 每个实体页带 YAML frontmatter，必填 `id` / `type` / `name` / `book`。
- `id` 用规范名，全书唯一；别名进 `aliases`。
- 关系写在人物 frontmatter 的 `relations`（`target` / `type` [/ `role`]）。
- `relations[].type` 必须取自下方受控词表，写错会被构建校验拦下。
- 妖怪扩展字段：`洞府` `原型` `能力` `法宝` `结局` `收服者`。
- 版本异文用 `variants`，矛盾用 `contradicts`（见第 6 节）。
- 重要度 `weight`（0–100）由 `/consolidate` 自动重算，勿手填。

### 关系受控词表（relation types）

```
亲属: 夫妻 父子 母子 兄弟 姐妹 祖孙 妯娌
社会: 主仆 师徒 师兄弟 同僚 朋友 结拜 君臣
情感: 情人 恋慕 仇敌 敌对
```

去重规则：双向关系（如「夫妻」）只存一条边；图谱由脚本统一去重。

---

## 5. 工作流（Operations）

每个操作都是一份分步清单，照做、不遗漏。

### 5.1 `/ingest` 摄取一回（核心循环）

1. 读 `src/content/chapters/<书>/0NN.md` 原文。
2. 与用户确认本回要点（登场人物、新妖怪、关键事件）。
3. 写 / 更新回目页 `chapters/<书>/0NN.md` 的 frontmatter（`characters` `locations` `summary`）。
4. 更新涉及的人物 / 妖怪页：补「关键情节」（带出处），补 `relations`。
5. 出现新人物 / 妖怪 / 地点 → 按对应 schema 建页。
6. 更新 `index.md`；在 `log.md` 追加：`## [日期] ingest | <书> 第NN回 标题`。
7. 提示用户：是否运行 `/graph` 重建关系数据。

### 5.2 `/graph` 重建关系图谱数据

- 运行 `python scripts/build_relations.py <书>`。
- 扫描该书全部人物 / 妖怪的 `relations`，去重、校验词表、合并矛盾边，
  输出 `src/data/<书>.relations.json`（`nodes` + `edges`）。

### 5.3 `/query` 回答提问

1. 先读对应书的 `index.md` 定位相关页。
2. 深入这些页面（必要时回查 `chapters/` 原文核对）。
3. 带出处作答，如（第27回 / chapters/西游记/027.md）。
4. 按下方「回填判断规则」决定是否沉淀；值得回填则建新页并更新 `index.md` 与 `log.md`。

#### 回填判断规则

**核心标准**：若删掉这次聊天记录会后悔丢了这个结论 → 回填；答完即弃 → 不回填。

**值得回填（满足任一即可）**：

| 信号 | 说明 | 存成什么 |
|------|------|----------|
| 合成型 | 综合 ≥3 个 wiki 页/回目才得出的结论 | `topics/<书>/` 新页 |
| 模板型 | 对比表、分类框架、时间线，以后还会复用 | `topics/<书>/` 新页 |
| 纠错型 | 发现页面间矛盾/缺口，query 中理清了 | 更新原页 + 必要时 `topics/` 说明 |
| 显式型 | 用户说「存一下」「回填进 wiki」 | 按用户指定 |

**不必回填**：

- 事实查表（某回出场、别名）→ 应更新已有人物/回目页，不另建页。
- 临时解释（某句古文意思）→ 聊天即可。
- 未定论草稿（「也许 A 和 B 有关？」）→ 等 ingest 或 `/dream` 再定稿。
- 纯主观感受（「你觉得这本书怎么样」）→ 非知识库内容。

**LLM 主动询问**：回答后，若满足合成型 / 模板型 / 纠错型任一，或用户用了「梳理 / 对比 / 总结 / 关系 / 脉络」等词，须主动问：

> 「这份分析涉及 N 个实体、M 条关系，要存成 `topics/<书>/XXX.md` 吗？」

用户确认后再写文件；未确认则不回填。

#### 回填页规范

路径：`src/content/topics/<书>/<主题名>.md`

```yaml
---
type: topic          # topic | 对比 | 分析
book: 金瓶梅
title: 西门庆官场网络
derived_from: [西门庆, 蔡御史, 第49回, 第50回]
created: 2026-06-14
tags: []
summary: 一句话说明本页价值
---
```

正文骨架：`## 结论` `## 论据（带出处）` `## 相关链接`（指向人物/回目页）。

`log.md` 追加：`## [日期] query-fill | <书> topics/<主题名>`。

**示例**：

| 提问 | 回填？ | 处理方式 |
|------|--------|----------|
| 第 49 回讲了什么 | ❌ | `/ingest` 更新回目页 |
| 西门庆怎么巴结蔡御史 | ⚠️ | 浅层复述 → 更新西门庆人物页；整条官场线 → `topics/西门庆官场网络.md` |
| 金瓶梅与红楼梦写家庭衰败有何不同 | ✅ | `topics/世情与贵族衰败对比.md`（跨书时可放主要涉及的那本，正文互链） |
| 「请巡按屈体求荣」什么意思 | ❌ | 聊天解释即可 |

### 5.4 `/lint` 体检（只发现，不改写）

扫描并产出一份「待办清单」，不直接改数据：

- 矛盾：页面间冲突的论断。
- 孤儿页：没有任何入链的实体。
- 缺页：被多次提及却没有独立页的重要实体（人物 / 地点）。
- 缺关系：A 页提到 B 却没建关系边。
- 字段缺漏：缺 `summary` / `first_appear` 等。
- 数据空白：可补充的方向。

**图鉴卡片语义**（喜好 / 信物·关键物品 / 金瓶梅·服饰）：`python scripts/audit_bestiary_semantics.py` 三书汇总；各书 `lint_report.py` 含「图鉴 · 人物…」与「图鉴 · JSON fields 语义」。规则见 `schema/character.md` · 实现见 `scripts/_item_wiki.py`。误填礼仪链/帮闲差事/部属 → `prune_*_likes.py` / `prune_*_keepsakes.py`；金瓶梅六房齐整服饰 → `prune_jpm_costumes.py`。

`/lint` 是 `/dream` 的待办来源之一。

### 5.5 `/dream` 睡眠巩固（主动改写，周期性）

与 `/lint` 的区别：**lint 只报告，dream 真改写**。攒一批数据（如整本 ingest 完）后跑一次：

1. **别名合并**：散落的「孙悟空 / 行者 / 齐天大圣」统一到一个 `id`，别名归并。
2. **补链接**：根据正文自动补全缺失的关系边。
3. **重算重要度**：按出场回数 / 关系数重算 `weight`（影响图谱节点大小、首页排序）。
4. **知识压缩**：把零散的逐回信息重新综合进人物页，使其反映全书而非流水账。
5. **跨版本巩固**：把异文整理进统一的 `variants` 块，建立 `contradicts` 边。
6. 完成后运行 `/graph`，并在 `log.md` 记录本次巩固范围。

### 5.6 `/guard` Trust Guard 校验（防幻觉）

运行 `python scripts/trust_guard.py <书>`，双层校验：

- **form（形式）**：frontmatter 字段合规（Astro 构建期 Zod 已强校验）。
- **content（内容）**：
  - `first_appear` 回目原文是否出现人物名（含 `CHARACTER_EXTRA_ANCHORS` 别称）
  - `## 关键情节` 各条是否在标注回目命中锚词（含人物弱校验 fallback）
  - `relations` 逐边：在情节回目 / `first_appear` 回目或全书回扫中双方是否同现
  - `transactions/`：`amount_normalized` 与 `source`（金瓶梅）
  查不到的标 `unverified` 并报告，不得凭空编造。

---

### 5.7 关系图谱前端（防空白，必守）

改顶栏、全站 CSS 或 `RelationGraph` / `GraphLayout` 时**必读** [`docs/关系图谱-前端布局规范.md`](docs/关系图谱-前端布局规范.md)。

铁律摘要：

1. **数据**：`RelationGraph` 内 `relationGraphForSlug(bookSlug)` 加载 JSON；**禁止**把整份 `*.relations.json` 塞进 `astro-island` props。
2. **高度**：保留 `--graph-chrome`（顶栏实测高度）+ `.graph-explorer` 的 `height/minHeight: calc(100dvh - var(--graph-chrome))`；**禁止**只靠 `height: 100%` 无显式 calc。
3. **初始化**：ECharts 用 ResizeObserver 等有尺寸再 init；勿无限 `requestAnimationFrame` 等 0 高度容器。
4. **底栏布局**（防「遮住 → 图消失」连锁）：
   - 阵营筛选 + 关系图例放在 **文档流** 底栏 `.graph-bottom-dock`（`flex-shrink: 0`），画布在 `.graph-chart-stage`（`flex: 1`）。
   - **禁止**两个底栏控件同用 `absolute bottom-*` 叠在同一位置；**禁止**用绝对定位底栏 + 画布 `bottom` 内缩去「让位」——阵营多时会吃掉全部高度，ECharts 容器变 0。
   - 详情侧栏用 `top + bottom` 锚在 `.graph-chart-stage` 内；**禁止** `height: 100vh`（与底栏 flex 布局冲突）。
   - 人物页链接统一 `characterHref(bookSlug, id)`（`encodeURIComponent`），勿手写 `/c/${id}`。
5. **改动分离**：底栏/CSS 与路由/`getStaticPaths`/链接函数 **分 PR、分验收**；404 先查 dev 是否在跑、`npm run dev:clean`，勿与布局回归混为一谈。
6. **验收（改完必做，三步）**：
   - 打开 `/honglou/graph`：无选中时节点/边可见；底栏阵营 + 关系图例均可见、互不遮挡。
   - 点击节点（如林黛玉）：侧栏出现；图谱仍在侧栏后方可见（非全屏空白）。
   - 点「查看人物页 →」或邻接链接：进入 `/honglou/c/林黛玉` 返回 200（非 Astro 火箭 404）。
   - 另跑 `npm run build` 通过。

空白图谱 ≠ 数据丢失；先查 canvas 父级 `clientHeight`。人物页 404 ≠ 缺 content；先查 dev 端口与 Vite 是否报 `astro:server-app.js` 错误。

---

## 6. 版本与矛盾建模（本库特色）

本库天然多版本：红楼梦 脂评本 vs 程高本；金瓶梅 词话本 vs 绣像本。把版本差异当一等公民。

人物 / 情节页中：

```yaml
variants:
  - edition: 脂评本
    claim: 后四十回散佚，结局靠探佚
    source: chapters/红楼梦/080
  - edition: 程高本
    claim: 黛玉焚稿断痴情，宝玉出家
    source: chapters/红楼梦/098
contradicts: [情节-黛玉结局]      # 标记存在版本冲突的主题 id
```

`/graph` 会把 `contradicts` 渲染成图谱里的「矛盾边」（虚线 / 异色），详情页并列展示异文。

---

## 7. 引用与风格

- 情节性结论必须标出处，如（第27回）。不得编造原文没有的情节。
- 引用原文保留原书字体（繁/简按原文）；你写的分析用简体。
- `summary` ≤ 2 句。
- 人物页骨架：`## 身份` `## 主要关系`（内链） `## 关键情节`（按回目带出处） `## 评析`。
- 回目页骨架：`## 梗概` `## 登场人物`（内链） `## 伏线/呼应` `## 出处`。

---

## 8. 可审计的演进

- 数据与本 schema 都纳入 git，每次操作产生可追溯的提交。
- `log.md` append-only，统一前缀 `## [YYYY-MM-DD] <op> | <范围>`，
  可用 `grep "^## \[" log.md | tail -5` 看最近动态。
- 修改本 `AGENTS.md` 或 schema 时，在 `log.md` 记一条 `schema` 变更说明。
- schema 与流程随使用共同演进：先跑通最小循环，再按不顺手处增补规则。

## 变更记录

- **2026-06-15**：§5.7 增补底栏 flex 铁律、侧栏锚定、链接编码、三步验收与布局/路由分离（2026-06 底栏遮挡→图消失→404 连锁复盘）。
- **2026-06-15**：§5.7 关系图谱前端布局铁律；[`docs/关系图谱-前端布局规范.md`](docs/关系图谱-前端布局规范.md)（防 ECharts 画布高度 0 复发）。
- **2026-06-14**：`/query` 增补「回填判断规则」、主题页 `topics/` 目录与 frontmatter 规范。
