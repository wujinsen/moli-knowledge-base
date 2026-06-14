# schema: chapter

回目页放在 `src/content/chapters/<书>/<NNN>.md`。frontmatter 是元数据，正文是原文（只读真相源）。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `type` | ✅ | 固定 `chapter` |
| `book` | ✅ | 红楼梦 \| 金瓶梅 \| 西游记 |
| `number` | ✅ | 回数（整数） |
| `title` | ✅ | 回目标题 |
| `characters` | | 本回登场人物 id 数组 |
| `locations` | | 本回涉及地点 **id** 数组（见 `locations/<书>/`） |
| `items` | | 本回涉及名物 **id** 数组（见 medicines/dishes/costumes/customs） |
| `summary` | | 本回梗概 |

## 正文

frontmatter 之后即原文正文。阅读器直接渲染。原文**只读**，整理只动 frontmatter。
