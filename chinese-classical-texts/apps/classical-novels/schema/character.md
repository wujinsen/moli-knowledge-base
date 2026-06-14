# schema: character / monster

人物页放在 `src/content/characters/<书>/<id>.md`。`type: monster` 为妖怪（西游记），比 character 多几字段。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 规范名，全书唯一 |
| `type` | ✅ | `character` \| `monster` |
| `name` | ✅ | 显示名 |
| `book` | ✅ | 红楼梦 \| 金瓶梅 \| 西游记 |
| `aliases` | | 别名数组 |
| `gender` | | 性别 |
| `faction` | | 阵营 / 家族（图谱着色用） |
| `first_appear` | | 首次登场，如 `第1回` |
| `status` | | 主角 \| 重要 \| 配角 |
| `tags` | | 标签数组 |
| `relations` | | 关系数组：`{ target, type, role? }` |
| `variants` | | 版本异文：`{ edition, claim, source? }` |
| `contradicts` | | 存在版本冲突的主题 id 数组 |
| `weight` | | 0–100，由 `/consolidate` 自动重算 |
| `summary` | | ≤ 2 句简介 |

## 妖怪扩展字段（type: monster）

`洞府` `原型` `能力[]` `法宝[]` `结局` `收服者`

## 示例

见 `src/content/characters/西游记/孙悟空.md`（character）与 `白骨精.md`（monster）。
