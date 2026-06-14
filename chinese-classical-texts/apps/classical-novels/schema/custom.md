# schema: custom / ritual / institution

民俗规章页放在 `src/content/customs/<书>/<id>.md` 或 topic 汇总。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 规范名 |
| `type` | ✅ | `festival` \| `wedding` \| `funeral` \| `ritual` \| `institution` \| `currency` |
| `name` | ✅ | 显示名 |
| `book` | ✅ | 红楼梦 |
| `participants` | | 参与者 id 数组 |
| `procedure` | | 礼仪程序数组 |
| `location` | | 地点 id |
| `economic` | | 费用/银两/物量 |
| `legal_norm` | | 礼制法度（如嫡庶、回九） |
| `first_appear` | | 回目 |
| `summary` | | ≤2句 |
