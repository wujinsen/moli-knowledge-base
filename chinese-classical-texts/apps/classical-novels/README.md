# 古典小说知识库（classical-novels）

基于 Karpathy「LLM Wiki」模式的古典小说知识库 + 可视化站点。
数据按书分（红楼梦 / 金瓶梅 / 西游记），应用统一一套。

- 维护规范见 [`AGENTS.md`](AGENTS.md)
- 数据模型见 [`schema/`](schema/)

## 架构

```
原文(chapters, 只读) → 结构化数据(characters/) → relations.json → Astro 站点
                         ↑ Trust Guard 校验   ↑ /consolidate 巩固
```

| 层 | 位置 |
|----|------|
| 原文（只读真相源） | `src/content/chapters/<书>/NNN.md` |
| 人物 / 妖怪 | `src/content/characters/<书>/*.md` |
| 书级元信息 | `src/content/books/<书>.md` |
| 关系图谱（生成物） | `src/data/<书>.relations.json` |
| 校验规则（代码） | `src/content.config.ts`（Zod） |

## 功能页面

- `/` 选书首页
- `/<slug>` 单书首页 + 目录
- `/<slug>/read/<回>` 阅读器
- `/<slug>/graph` 人物关系图谱（ECharts，含矛盾边）
- `/<slug>/bestiary` 人物 / 妖怪图鉴
- `/<slug>/c/<id>` 人物 / 妖怪详情

slug：红楼梦=honglou，金瓶梅=jinpingmei，西游记=xiyouji。

## 快速开始

```bash
# 1. 安装前端依赖
npm install

# 2. 安装 Python 依赖（脚本用）
pip install -r requirements.txt

# 3. 生成关系图谱数据
python scripts/build_relations.py 西游记

# 4. 启动开发服务器
npm run dev
```

## 数据维护脚本

| 命令 | 作用 |
|------|------|
| `python scripts/import_chapters.py <书>` | 把已有知识库原文导入 chapters |
| `python scripts/build_relations.py [书]` | `/graph`：生成 relations.json |
| `python scripts/trust_guard.py [书]` | `/guard`：内容出处校验（防幻觉） |
| `python scripts/lint_kb.py [书]` | `/lint`：items/摘要/字段体检（只报告） |
| `python scripts/clean_chapter_items.py [书]` | 从 items[] 剔除 location 重复 |
| `python scripts/consolidate.py [书] [--write]` | `/dream`：重算重要度、查别名冲突 |

日常维护循环（Ingest → Query → Lint → dream）详见 `AGENTS.md`。

### 维护台 Studio（MVP）

```bash
# 终端 A
npm run studio:api

# 终端 B
npm run dev
```

- 模块页：`/{slug}/studio` → **实体工作区** | **批处理**（`/lint` `/graph` `/dream` `/guard` 已接）
- 人物页 dev 深链：`/{slug}/studio?entity=…`
- 协议：`docs/维护台-聊天协议.md`
- API：`apps/kb-orchestrator/`
