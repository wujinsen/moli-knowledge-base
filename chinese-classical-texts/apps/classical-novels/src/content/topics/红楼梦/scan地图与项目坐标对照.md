---
type: topic
book: 红楼梦
title: scan 地图与项目坐标对照
derived_from: [大观园建筑名录, 大观园地图, raw/scan]
created: 2026-06-15
tags: [地图, scan, 坐标]
summary: raw/scan 等距参考图 23 处编号与本库 garden 节点的对照；方位以 seed_garden_coords 为准。
---

## 结论

`chinese-classical-texts/raw/scan/` 内仅有一张 **AI 生成等距示意图**（非 `.glb` / 网格模型），编号 1–23。可复刻其 **绢本工笔视觉风格**，但 **不可采信其建筑方位**。

本库 `/honglou/scene` 与 `/honglou/map` 共用 `locations/红楼梦/*.md` 中的 `coord` + `garden_zone`（`seed_garden_coords.py` 写入），以「南北中轴说」inference 布局。

## 对照表

| 图号 | scan 标注 | 本库 id | 匹配 |
|------|-----------|---------|------|
| 1 | 正门/大门 | [曲径通幽](/honglou/l/曲径通幽) | 部分（南门入口） |
| 2 | 仪门 | — | 园外（荣府） |
| 3 | 大草厅 | [省亲别墅](/honglou/l/省亲别墅) | 部分 |
| 4 | 荣禧堂 | — | 园外（荣府） |
| 5 | 薛芳斋 | [蘅芜苑](/honglou/l/蘅芜苑) | 别名 |
| 6 | 潇湘馆 | [潇湘馆](/honglou/l/潇湘馆) | ✓ |
| 7 | 蘅芜苑 | [蘅芜苑](/honglou/l/蘅芜苑) | ✓ |
| 8 | 秋爽斋 | [秋爽斋](/honglou/l/秋爽斋) | ✓ |
| 9 | 稻香村 | [稻香村](/honglou/l/稻香村) | ✓ |
| 10 | 缀锦楼 | [缀锦楼](/honglou/l/缀锦楼) | ✓ |
| 11 | 怡红院 | [怡红院](/honglou/l/怡红院) | ✓ |
| 12 | 凸碧山庄 | [凸碧堂](/honglou/l/凸碧堂) | 别名 |
| 13 | 藕香榭 | [藕香榭](/honglou/l/藕香榭) | ✓ |
| 14 | 暖香坞 | [暖香坞](/honglou/l/暖香坞) | ✓ |
| 15 | 水月庵 | — | 园外 |
| 16 | 时恩院 | [栊翠庵](/honglou/l/栊翠庵) | 待考 |
| 17 | 澄瑞阁 | [缀锦阁](/honglou/l/缀锦阁) | 部分 |
| 18 | 放鹤亭 | [滴翠亭](/honglou/l/滴翠亭) 或 [沁芳亭](/honglou/l/沁芳亭) | 部分 |
| 19 | 芳官建 | [红香圃](/honglou/l/红香圃) | 部分 |
| 20 | 花溆 | [蓼溆](/honglou/l/蓼溆) | 别名 |
| 21 | 曲径通幽 | [曲径通幽](/honglou/l/曲径通幽) | ✓ |
| 22 | 柳堤 | — | 未单列节点 |
| 23 | 夹道 | — | 园外（荣府） |

机器可读对照：`src/data/红楼梦.garden_scan_ref.json`。

## 复刻策略

1. **坐标**：`python scripts/build_garden_scene_manifest.py --write` 从全部 `garden_zone` 节点生成 `红楼梦.garden_scene_full.json`。
2. **渲染**：Pixi 等距占位 + 已有三院 sprite；其余按 `zone` 着色。
3. **参考图**：`public/honglou/scene/scan-reference.png` 在实景页弹窗对照，不参与落位。

## 相关链接

- [大观园建筑名录](/honglou/t/大观园建筑名录)
- [大观园地图](/honglou/map) · [大观园实景](/honglou/scene)
- [大观园建筑图纸与美术资料来源](/honglou/t/大观园建筑图纸与美术资料来源)
