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

`性格` · `喜好[]`（法宝 id 可链 `/xiyouji/i/{id}`）· `结局`

数据：`scripts/xyj_bestiary_fields.py` → `build_xyj_bestiary_json.py`（含 `outcome_extract`）→ `xiyouji.bestiary.json` · 同步 `seed_xyj_bestiary.py`

## 红楼梦图鉴扩展（type: character）

`性格` · `喜好[]`（条目可为名物 id、活动或人物名；名物 id 可链至 `/honglou/i/{id}`）· `结局`

数据：`scripts/hlm_bestiary_fields.py` → `build_hlm_bestiary_json.py`（含 `outcome_extract` 自动补全）→ `hongloumeng.bestiary.json` · 同步 `seed_hlm_bestiary.py`

## 图鉴分组（三书共用）

各书 `src/data/<书>.bestiary.json` 可含 `groups`：`{ "组名": ["人物id", ...] }`。页面由 `src/lib/bestiaryGroups.ts` 统一解析；未配置 `groups` 时回退 `faction` 分组。

| 书 | 数据文件 | 校验 |
|----|----------|------|
| 红楼梦 | `hongloumeng.bestiary.json` | `validate_bestiary_groups.py` |
| 金瓶梅 | `jinpingmei.bestiary.json` | 同上 |
| 西游记 | `xiyouji.bestiary.json` | 同上（人物+妖怪统一分组） |

### 分类规则

`groups` 是**人工编排的名册**，不是按某个字段自动算出来的。划分维度是「**身份等级 + 所属支系/线索 + 与主角的亲疏**」的混合：

- **顺序即渲染顺序**：`groups` 里组的先后，就是图鉴页分区从上到下的顺序；组内人物按 `weight` 降序排。
- **兜底组**：未列入任何组的人物，由 `groupByCatalog` 归入末尾的「其他人物 / 其他」（`restLabel`）。
- **去重**：一个 id 只应出现在一个组里；`validate_bestiary_groups.py` 会拦下重复。
- 编排数据由各书脚本生成：红楼 `hlm_bestiary_fields.py` 的 `GROUPS` → `build_hlm_bestiary_json.py`；金瓶 / 西游同理。

红楼梦现有 8 组及其收录规则（示例）：

| 组 | 收录规则 |
|----|----------|
| 金陵十二钗 | 严格按太虚幻境「正册十二钗」名单（仅 12 人） |
| 宝玉与近侍 | 贾宝玉本人 + 怡红院贴身丫鬟小厮 |
| 尊长与主子 | 荣国府与薛家的长辈 / 主子辈 |
| 宁国府 | 宁国府一支 |
| 丫鬟与近侍 | 其他各房的丫鬟仆妇（非怡红院） |
| 清客房官仆 | 清客相公、大夫、僧道、管家仆役 |
| 族亲与外客 | 贾府旁支子弟 + 外面来往的世家王公 |
| 楔子与刘姥姥线 | 第一回神话楔子 + 刘姥姥进府线 |

> 「宝玉与近侍」与「丫鬟与近侍」的切分依据：**服侍对象是否为宝玉 / 怡红院**（晴雯入前者、紫鹃入后者）。

### 页面交互

图鉴页 `src/pages/[book]/bestiary.astro`：每个分组渲染为可折叠的 `<details class="bestiary-group">`（默认展开），顶部「全部人物名录」上方有一条**全部展开 / 全部折叠**总控（`[data-bestiary-expand]`，纯客户端脚本切换所有分组的 `open`）。

## 示例

见 `src/content/characters/西游记/孙悟空.md`（character）与 `白骨精.md`（monster）。
