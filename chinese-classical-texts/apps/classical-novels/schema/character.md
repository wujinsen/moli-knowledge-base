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

## 金瓶梅图鉴扩展（type: character）

`ximen_proximity`（亲缘 / 雇佣 / 利益交换 / 外人）· `靠山` · `依附` · `结局`

数据：`scripts/jpm_bestiary_fields.py` → `build_jpm_bestiary_json.py` → `jinpingmei.bestiary.json` · 同步 `seed_jpm_bestiary.py`

## 西游记图鉴扩展

`性格` · `喜好[]`（法宝 id 可链 `/xiyouji/i/{id}`）

数据：`scripts/xyj_bestiary_fields.py` → `build_xyj_bestiary_json.py` → `xiyouji.bestiary.json` · 同步 `seed_xyj_bestiary.py`

## 红楼梦图鉴扩展（type: character）

`性格` · `喜好[]`（条目可为名物 id、活动或人物名；名物 id 可链至 `/honglou/i/{id}`）

数据：`scripts/hlm_bestiary_fields.py` → `build_hlm_bestiary_json.py` → `hongloumeng.bestiary.json`（132 人）· 同步 `seed_hlm_bestiary.py`

## 图鉴分组（三书共用）

各书 `src/data/<书>.bestiary.json` 可含 `groups`：`{ "组名": ["人物id", ...] }`。页面由 `src/lib/bestiaryGroups.ts` 统一解析；未配置 `groups` 时回退 `faction` 分组。

| 书 | 数据文件 | 校验 |
|----|----------|------|
| 红楼梦 | `hongloumeng.bestiary.json` | `validate_bestiary_groups.py` |
| 金瓶梅 | `jinpingmei.bestiary.json` | 同上 |
| 西游记 | `xiyouji.bestiary.json` | 同上（人物+妖怪统一分组） |

## 示例

见 `src/content/characters/西游记/孙悟空.md`（character）与 `白骨精.md`（monster）。
