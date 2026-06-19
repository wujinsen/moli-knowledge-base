// 按需引入 ECharts：仅注册本项目实际用到的图表/组件/渲染器，
// 替代 `import * as echarts from 'echarts'` 的全量打包（~1.1MB → ~0.4MB）。
//
// 全站审计（10 个图表组件）：
//   图表类型：graph / bar / line / scatter / sankey
//   组件：tooltip / grid(xAxis,yAxis) / legend / markArea / title
//   API：仅 echarts.init（无 graphic / 地图 / 主题注册）
// 新增图表类型或组件时，请在此处补 use([...])，否则对应图表会静默不渲染。
import * as echarts from 'echarts/core';
import { BarChart, GraphChart, LineChart, SankeyChart, ScatterChart } from 'echarts/charts';
import {
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsOption } from 'echarts';

echarts.use([
  BarChart,
  GraphChart,
  LineChart,
  SankeyChart,
  ScatterChart,
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TitleComponent,
  TooltipComponent,
  CanvasRenderer,
]);

export { echarts };
export type { EChartsOption };
