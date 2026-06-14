# schema: topic（/query 回填页）

主题 / 对比 / 分析页放在 `src/content/topics/<书>/<主题名>.md`。
由 `/query` 产生，不由 `/ingest` 直接写。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | `topic` \| `对比` \| `分析` |
| `book` | ✅ | 红楼梦 \| 金瓶梅 \| 西游记 |
| `title` | ✅ | 页面标题 |
| `derived_from` | | 来源实体/回目 id 数组 |
| `created` | | YYYY-MM-DD |
| `tags` | | 标签 |
| `summary` | | ≤ 2 句，说明本页价值 |

## 正文骨架

- `## 结论`
- `## 论据（带出处）`
- `## 相关链接`（指向 characters / chapters）

## 何时建页

见 `AGENTS.md` §5.3「回填判断规则」。不确定时 LLM 须先问用户是否存。
