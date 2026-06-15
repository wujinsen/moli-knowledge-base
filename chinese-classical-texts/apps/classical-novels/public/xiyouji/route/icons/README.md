# 取经路线 · 节点图标

`/xiyouji/route/icons` 下图标会按地点 `id` 自动加载；**缺失时按 `realm` 回退**，无需改代码。

| 文件名 | 地点 |
|--------|------|
| `chang-an.png` | 长安城 |
| `huoyanshan.svg` | 火焰山 |
| `leiyin.svg` | 灵山·大雷音寺 |
| `liushahe.svg` | 流沙河 |
| `longgong.svg` | 东海龙宫 |
| `lingxiao.svg` | 灵霄宝殿 |
| `diyu.svg` | 幽冥地府 |
| `putuo.svg` | 普陀山 |
| … | 见 `src/lib/routeIcons.ts` |

重生成示意 SVG：`python scripts/gen_route_icons.py`

替换为手绘/AI 素材时保持文件名不变即可。
