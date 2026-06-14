# schema: medicine / prescription

医药页放在 `src/content/medicines/<书>/<id>.md`。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 规范名 |
| `type` | ✅ | `medicine` \| `prescription` \| `diagnosis` |
| `name` | ✅ | 显示名 |
| `book` | ✅ | 红楼梦 |
| `category` | | 丸散汤膏 / 诊脉 / 病症 |
| `patient` | | 用药/患病人物 id |
| `prescriber` | | 开方者（和尚、大夫名） |
| `physician` | | 诊脉大夫 id |
| `ingredients` | | 药材/配料数组 |
| `process` | | 制法 |
| `syndrome` | | 证候（如热毒、水亏木旺） |
| `pulse` | | 脉案原文摘要 |
| `effect_literary` | | 情节/象征功能 |
| `effect_scholarly` | | 学者/医学史评价（标注 inference） |
| `first_appear` | | 如 `第7回` |
| `appear_in` | | 回目数组 |
| `summary` | | ≤2句 |

## 示例

`src/content/medicines/红楼梦/冷香丸.md`
