# chinese-classical-texts（中国古籍）

LLM Wiki 领域单元：原始文档（raw）→ wiki 维护 → 前端展示（apps）。

## 目录

```
chinese-classical-texts/
  raw/              只读真相源，按来源分类，永不重排
    daizhige/       殆知阁 v20（10 藏）
    editions/       自有校订/善本（含影印 LaTeX 工程）
    scan/           纯影印图片
    external/       其它零散来源
  wiki/             LLM 维护页（index / topics / log）
  apps/
    classical-novels/   章回叙事前端 + schema
  scripts/          raw 抓取与校验脚本
  docs/             域规划文档
    daizhige-catalog/   殆知阁 15694 册书目索引（运行 scripts/build_daizhige_catalog.py 可重建）
```

## 文档

| 文档 | 说明 |
|------|------|
| [`docs/功能总览.md`](docs/功能总览.md) | **迄今已落地 + 已规划功能一览（本文档入口）** |
| [`docs/红楼梦-知识图谱架构.md`](docs/红楼梦-知识图谱架构.md) | **四维图谱：人物/时空/物质/文本意象** |
| [`docs/金学分支与产品映射.md`](docs/金学分支与产品映射.md) | **金学五维度 → 产品模块** |
| [`docs/金瓶梅-知识图谱架构.md`](docs/金瓶梅-知识图谱架构.md) | 世情/政商/物价/名物图谱 |
| [`docs/图谱可视化方案.md`](docs/图谱可视化方案.md) | 关系图谱 V1 特效与 G6 演进 |
| [`docs/西游学分支与产品映射.md`](docs/西游学分支与产品映射.md) | **西游学五维度 → 产品模块** |
| [`../docs/2026智能知识库演进路线.md`](../docs/2026智能知识库演进路线.md) | 2026 五能力 · S0~S5 演进 |
| [`docs/技术方案.md`](docs/技术方案.md) | 总体架构、技术栈、数据模型、路线图 |
| [`docs/产品功能规划.md`](docs/产品功能规划.md) | 三大名著读者/学者/师生功能蓝图与分期 |
| [`docs/红学分支与产品映射.md`](docs/红学分支与产品映射.md) | 红学考证/文学/名物 → 产品模块与建设优先级 |
| [`docs/红楼梦-饮食纵切研究.md`](docs/红楼梦-饮食纵切研究.md) | 饮食纵切（方法论+本体+功能） |
| [`docs/红楼梦-医药饮食研究.md`](docs/红楼梦-医药饮食研究.md) | 医药与饮食名物研究 |
| [`docs/红楼梦-服饰民俗规章研究.md`](docs/红楼梦-服饰民俗规章研究.md) | 服饰、民俗、规章 |
| [`docs/红楼梦-建筑园林学考证.md`](docs/红楼梦-建筑园林学考证.md) | 大观园园林考证 |
| [`docs/红楼梦-建筑居所研究.md`](docs/红楼梦-建筑居所研究.md) | 建筑与居所 |
| [`docs/红楼梦-大观园沉浸体验.md`](docs/红楼梦-大观园沉浸体验.md) | 2D 地图 + 3D 漫游 + NPC 对话 |
| [`docs/知识库域规划.md`](docs/知识库域规划.md) | 殆知阁 → 实体家族映射 |
| [`docs/知识库组织方案.md`](docs/知识库组织方案.md) | 多领域分治原则 |
| [`docs/daizhige-catalog/`](docs/daizhige-catalog/) | 15694 册书目索引 |
| [`apps/classical-novels/AGENTS.md`](apps/classical-novels/AGENTS.md) | 维护宪法 |

## 工作流

见 `apps/classical-novels/AGENTS.md`：`/ingest` `/graph` `/query` `/lint` `/dream` `/guard`。

参考：[Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
