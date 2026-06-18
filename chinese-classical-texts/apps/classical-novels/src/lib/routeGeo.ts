/** 取经路线 · 真实经纬度 → 方位布局 + 路段距离 */

export interface GeoPoint {
  lat: number;
  lng: number;
}

const RAD = Math.PI / 180;
const EARTH_R_KM = 6371;

/** 大圆距离（km） */
export function haversineKm(a: GeoPoint, b: GeoPoint): number {
  const dLat = (b.lat - a.lat) * RAD;
  const dLng = (b.lng - a.lng) * RAD;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(a.lat * RAD) * Math.cos(b.lat * RAD) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_R_KM * Math.asin(Math.min(1, Math.sqrt(s)));
}

/** 方位角（度）：0=北，90=东，180=南，270=西 */
export function bearingDeg(from: GeoPoint, to: GeoPoint): number {
  const φ1 = from.lat * RAD;
  const φ2 = to.lat * RAD;
  const Δλ = (to.lng - from.lng) * RAD;
  const y = Math.sin(Δλ) * Math.cos(φ2);
  const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

const BEARING_LABELS = ['北', '东北', '东', '东南', '南', '西南', '西', '西北'] as const;

export function bearingLabel(deg: number): string {
  return BEARING_LABELS[Math.round(deg / 45) % 8];
}

/** 传统里数（约 1 里 ≈ 0.5 km） */
export function kmToLi(km: number): number {
  return Math.round(km * 2);
}

export function formatSegment(from: GeoPoint, to: GeoPoint): { km: number; li: number; bearing: string } {
  const km = haversineKm(from, to);
  return { km: Math.round(km), li: kmToLi(km), bearing: bearingLabel(bearingDeg(from, to)) };
}

/** 凡间站点 → 今地/丝路比附（非测绘定稿，供真实地理视图标注） */
export const GEO_ANCHORS: Record<string, string> = {
  长安城: '西安',
  两界山: '陕甘界',
  鹰愁涧: '陇西',
  高老庄: '甘南',
  黄风岭: '陇东',
  流沙河: '洮河',
  五庄观: '河西',
  白虎岭: '河西走廊',
  莲花洞: '河西走廊',
  乌鸡国: '青海东',
  火云洞: '青海',
  车迟国: '青海西',
  通天河: '通天河',
  西梁女国: '青海西南',
  火焰山: '吐鲁番',
  祭赛国: '塔里木南缘',
  荆棘岭: '昆仑北麓',
  小雷音寺: '于阗一带',
  朱紫国: '昆仑山麓',
  狮驼岭: '帕米尔东',
  比丘国: '喀什噶尔',
  灭法国: '帕米尔西',
  玉华州: '兴都库什',
  金平府: '兴都库什',
  天竺国: '北方邦',
  灵山: '菩提伽耶',
};

export function geoAnchor(id: string): string | null {
  return GEO_ANCHORS[id] ?? null;
}

export function formatGeoCoord(geo: GeoPoint): string {
  const latH = geo.lat >= 0 ? 'N' : 'S';
  const lngH = geo.lng >= 0 ? 'E' : 'W';
  return `${Math.abs(geo.lat).toFixed(2)}°${latH} · ${Math.abs(geo.lng).toFixed(2)}°${lngH}`;
}

/** 真实地理视图：小说名 + 比附今地 */
export function geoMapLabel(id: string, name: string, order: number | null): string {
  const short = name.replace(/^.*·/, '');
  const anchor = geoAnchor(id);
  const prefix = order != null ? `${order} ` : '';
  return anchor ? `${prefix}${short}→${anchor}` : `${prefix}${short}`;
}

/** 画布坐标方位（y 向下为正，示意图北在上） */
export function canvasBearing(from: { x: number; y: number }, to: { x: number; y: number }): string {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  if (dx === 0 && dy === 0) return '—';
  const deg = ((Math.atan2(dx, -dy) * 180) / Math.PI + 360) % 360;
  return bearingLabel(deg);
}

/** 示意图视图：回目序 + 小说地名（神话层不加序号） */
export function schematicMapLabel(name: string, order: number | null, isReal: boolean): string {
  const short = name.replace(/^.*·/, '');
  if (isReal && order != null) return `${order}·${short}`;
  return short;
}

/** @deprecated 示意图已改用独立叙事 coord；仅作缺 coord 时的兜底 */
export function projectRouteLayout<
  T extends { id: string; layer: string; geo?: GeoPoint; x: number; y: number },
>(
  nodes: T[],
  originId = '长安城',
  width = 1000,
  height = 640,
  padding = 55,
): void {
  const origin = nodes.find((n) => n.id === originId)?.geo;
  if (!origin) return;

  const cosLat = Math.cos(origin.lat * RAD);
  const projected: { id: string; px: number; py: number }[] = [];

  for (const n of nodes) {
    if (n.layer !== 'real' || !n.geo) continue;
    projected.push({
      id: n.id,
      px: (n.geo.lng - origin.lng) * cosLat,
      py: n.geo.lat - origin.lat,
    });
  }
  if (projected.length < 2) return;

  const minPx = Math.min(...projected.map((p) => p.px));
  const maxPx = Math.max(...projected.map((p) => p.px));
  const minPy = Math.min(...projected.map((p) => p.py));
  const maxPy = Math.max(...projected.map((p) => p.py));
  const spanX = maxPx - minPx || 1;
  const spanY = maxPy - minPy || 1;
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;
  const scale = Math.min(innerW / spanX, innerH / spanY);

  const byId = new Map(projected.map((p) => [p.id, p]));
  for (const n of nodes) {
    if (n.layer !== 'real' || !n.geo) continue;
    const p = byId.get(n.id)!;
    n.x = padding + (p.px - minPx) * scale;
    n.y = padding + (maxPy - p.py) * scale;
  }
}
