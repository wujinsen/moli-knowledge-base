/**
 * 大观园实景与 ECharts 地图（seed_garden_coords.py）共用逻辑坐标。
 * x：西小东大；y：北小南大（与 /honglou/map 一致）。
 */
export const GARDEN_LOGICAL_BOUNDS = {
  minX: 115,
  maxX: 740,
  minY: 85,
  maxY: 535,
} as const;

export interface LogicalPoint {
  x: number;
  y: number;
}

export function logicalToScene(
  lx: number,
  ly: number,
  sceneWidth: number,
  sceneHeight: number,
  padding = { x: 100, y: 80 },
): LogicalPoint {
  const { minX, maxX, minY, maxY } = GARDEN_LOGICAL_BOUNDS;
  const ux = sceneWidth - padding.x * 2;
  const uy = sceneHeight - padding.y * 2;
  return {
    x: padding.x + ((lx - minX) / (maxX - minX)) * ux,
    y: padding.y + ((ly - minY) / (maxY - minY)) * uy,
  };
}

/** 逻辑坐标系下两点「步数」（与 seed 图同一量纲：1 单位 ≈ px_per_step 步） */
export function logicalSteps(a: LogicalPoint, b: LogicalPoint, pxPerStep: number): number {
  return Math.round(Math.hypot(b.x - a.x, b.y - a.y) / pxPerStep);
}

/** 地图/实景页统一免责声明（inference 坐标，非测绘） */
export const GARDEN_LAYOUT_DISCLAIMER =
  '坐标属红学 inference（南北中轴说）；第17回游线顺序来自正文。院间「步数」为逻辑换算，非测绘尺度，不可与原文丈尺对勘。scan/复原园图不参与落位。';

/** 相对方位（北在上；y 增大为向南） */
export function bearingLabel(from: LogicalPoint, to: LogicalPoint): string {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  if (Math.hypot(dx, dy) < 8) return '此处';
  // y 北小南大：目标在 from 之北时 dy<0，须用 -dy 使 0°=北
  const deg = (Math.atan2(dx, -dy) * 180) / Math.PI;
  const dirs = ['北', '东北', '东', '东南', '南', '西南', '西', '西北'] as const;
  const idx = Math.round(deg / 45);
  return dirs[((idx % 8) + 8) % 8];
}
