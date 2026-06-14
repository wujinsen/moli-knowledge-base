# schema: location / building

地点页放在 `src/content/locations/<书>/<id>.md`。涵盖府邸、花园、院落、亭台、庵祠、幻境等空间实体。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 规范名，全书唯一 |
| `type` | ✅ | `location` \| `building` \| `garden` \| `temple` \| `realm` |
| `name` | ✅ | 显示名 |
| `book` | ✅ | 红楼梦 \| 金瓶梅 \| 西游记 |
| `aliases` | | 别名、曾用匾额数组 |
| `category` | | 府邸 \| 花园 \| 院落 \| 亭 \| 楼 \| 阁 \| 榭 \| 庵 \| 祠 \| 闸 \| 幻境 \| 市街 \| 其他 |
| `parent` | | 上级地点 id（如 潇湘馆 → 大观园） |
| `occupants` | | 主要居住/使用者 id 数组（人物或机构） |
| `nearby` | | 邻近地点 id 数组 |
| `plaque` | | 正式匾额名 |
| `couplet` | | 对联：`{ upper, lower }` |
| `features` | | 环境、格局特征数组 |
| `furnishings` | | 主要陈设数组 |
| `plants` | | 主要植物数组 |
| `first_appear` | | 首次出现，如 `第17回` |
| `appear_in` | | 重要出场回目数组 |
| `tags` | | 标签数组 |
| `summary` | | ≤ 2 句简介 |

## 正文骨架

```
## 位置与格局
## 居住者 / 关联人物
## 关键情节（带出处）
## 评析
```

## 与回目的关系

回目 frontmatter 的 `locations[]` 存本回涉及的地点 **id**，不写内联描述。详细数据在本 schema 页面维护。

## 示例

见 `src/content/locations/红楼梦/大观园.md`、`潇湘馆.md`。
