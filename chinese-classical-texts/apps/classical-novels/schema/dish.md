# schema: dish / banquet / ingredient

饮食页放在 `src/content/dishes/<书>/<id>.md`。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 规范名 |
| `type` | ✅ | `dish` \| `banquet` \| `tea` \| `wine` \| `ingredient` |
| `name` | ✅ | 显示名 |
| `book` | ✅ | 红楼梦 |
| `category` | | 主食/点心/汤羹/药膳/节令 |
| `ingredients` | | 食材数组 |
| `process` | | 工艺步骤 |
| `cost_estimate` | | 估价（两/文/「十来只鸡」等原文单位） |
| `temperature` | | 寒热属性（inference 须标注） |
| `diet_axes` | | 营养结构轴手标（覆盖关键词误判）；键见 `fine_tonic` `fat_sweet` `refined_grain` `coarse_balance` `feast_luxury` `alcohol`，值 0–5 |
| `eaters` | | 食用者 id 数组 |
| `location` | | 地点 id |
| `occasion` | | 场合/节令 |
| `literary_vs_real` | | `literary` \| `plausible_qing` \| `disputed` |
| `first_appear` | | 回目 |
| `summary` | | ≤2句 |

## 示例

`src/content/dishes/红楼梦/茄鲞.md`
