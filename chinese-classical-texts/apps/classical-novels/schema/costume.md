# schema: costume / accessory

服饰页放在 `src/content/costumes/<书>/<id>.md`。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 规范名 |
| `type` | ✅ | `costume` \| `accessory` \| `fabric` |
| `name` | ✅ | 显示名 |
| `book` | ✅ | 红楼梦 |
| `wearer` | | 穿着/佩戴者 |
| `material` | | 材质（软烟罗、雀金等） |
| `color` | | 颜色 |
| `occasion` | | 场合 |
| `rank_signal` | | 阶层信号 |
| `first_appear` | | 回目 |
| `description` | | 原文描写摘要 |
| `summary` | | ≤2句 |
