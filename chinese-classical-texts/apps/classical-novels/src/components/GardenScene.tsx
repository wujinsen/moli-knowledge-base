import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Application,
  Assets,
  Container,
  FillGradient,
  Graphics,
  Rectangle,
  Sprite,
  Text,
  TilingSprite,
  type Texture,
} from 'pixi.js';
import { graphTheme } from '../lib/graphTheme';
import {
  bearingLabel,
  GARDEN_LAYOUT_DISCLAIMER,
  logicalSteps,
  logicalToScene,
  type LogicalPoint,
} from '../lib/gardenSceneCoords';

interface SceneBuilding {
  id: string;
  name: string;
  plaque?: string;
  zone: string;
  logical: LogicalPoint;
  x: number;
  y: number;
  w: number;
  h: number;
  sprite?: string;
  link?: string;
  note?: string;
}

interface SceneNpc {
  id: string;
  name: string;
  at?: string;
  logical: LogicalPoint;
  x: number;
  y: number;
  sprite?: string;
  link?: string;
  tint?: string;
}

interface ScenePath {
  from: string;
  to: string;
}

export interface GardenSceneData {
  title: string;
  subtitle?: string;
  width: number;
  height: number;
  /** 旧：整园 AI 大图当画布底图。沙盘模式下不再使用，保留兼容。 */
  background?: string;
  /** 美术画廊：整园 AI 工笔大图，仅作展示弹窗（方位仅示意）。 */
  gallery?: string;
  scan_reference?: string;
  px_per_step: number;
  coord_basis?: string;
  scale_note?: string;
  buildings: Array<Omit<SceneBuilding, 'x' | 'y'> & { logical: LogicalPoint; x?: number; y?: number }>;
  npcs: Array<Omit<SceneNpc, 'x' | 'y'> & { logical: LogicalPoint; x?: number; y?: number }>;
  paths: ScenePath[];
}

export interface DialogueLine {
  text: string;
  chapter: number;
  source: string;
}

interface Props {
  scene: GardenSceneData;
  pools: Record<string, DialogueLine[]>;
  bookSlug: string;
}

const ZONE_FILL: Record<string, number> = {
  居所: 0xb45f7a,
  水系: 0x3f7fa6,
  仪典: 0xb08416,
  亭榭: 0x7c5fb0,
  寺观: 0x5c7a9c,
  路径: 0x6b7280,
  服务: 0x596273,
};

/** 写实等距美术资产（与 daguanyuan-full-bg-scan-style.png 同调；坐标仍用项目数据） */
const SCENE_ASSETS = {
  grass: '/honglou/scene/grass.png',
  trees: '/honglou/scene/trees.png',
  lotusPad: '/honglou/scene/lotus-pad.png',
  lotusBloom: '/honglou/scene/lotus-bloom.png',
  rockA: '/honglou/scene/rock-a.png',
  rockB: '/honglou/scene/rock-b.png',
  rockC: '/honglou/scene/rock-c.png',
  grandhall: '/honglou/scene/grandhall.png',
  courtyard: '/honglou/scene/courtyard.png',
  farmstead: '/honglou/scene/farmstead.png',
  temple: '/honglou/scene/temple.png',
  xie: '/honglou/scene/xie.png',
  pavilion: '/honglou/scene/pavilion.png',
  bridge: '/honglou/scene/bridge.png',
  cottage: '/honglou/scene/cottage.png',
} as const;

type ArchetypeKey =
  | 'grandhall'
  | 'courtyard'
  | 'farmstead'
  | 'temple'
  | 'xie'
  | 'pavilion'
  | 'bridge'
  | 'cottage';

/** 按 id/名称/分区为每栋建筑选一个等距 sprite 原型 */
function archetypeFor(b: { id: string; name: string; zone: string }): ArchetypeKey {
  const { id, name, zone } = b;
  if (id === '省亲别墅') return 'grandhall';
  if (id === '稻香村') return 'farmstead';
  if (/桥|石梯/.test(name)) return 'bridge';
  if (/榭|堂|厅|阁/.test(name)) return 'xie';
  switch (zone) {
    case '仪典':
      return 'grandhall';
    case '居所':
      return 'courtyard';
    case '亭榭':
      return /亭/.test(name) ? 'pavilion' : 'xie';
    case '水系':
      if (/亭/.test(name)) return 'pavilion';
      if (/闸/.test(name)) return 'bridge';
      if (/坞/.test(name)) return 'cottage';
      return 'pavilion';
    case '寺观':
      return 'temple';
    case '路径':
      return 'bridge';
    case '服务':
      return 'cottage';
    default:
      return 'courtyard';
  }
}

function center(b: SceneBuilding) {
  return { x: b.x + b.w / 2, y: b.y + b.h / 2 };
}

/** 确定性随机（沙盘林木散点用，保证每次构建一致、可复现） */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 点到线段最近距离及投影点 */
function nearestOnSegment(
  px: number,
  py: number,
  ax: number,
  ay: number,
  bx: number,
  by: number,
): { x: number; y: number; dist: number } {
  const dx = bx - ax;
  const dy = by - ay;
  const len2 = dx * dx + dy * dy || 1e-6;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2));
  const x = ax + dx * t;
  const y = ay + dy * t;
  return { x, y, dist: Math.hypot(px - x, py - y) };
}

/** 最近水域接触点（溪心/池缘），用于倒影定位 */
function nearestWaterPoint(
  px: number,
  py: number,
  streamLines: Array<[LogicalPoint, LogicalPoint]>,
  poolCenters: Array<{ x: number; y: number; r: number }>,
  streamR: number,
): { x: number; y: number; dist: number } | null {
  let best: { x: number; y: number; dist: number } | null = null;
  const reach = streamR + 58;
  for (const [a, b] of streamLines) {
    const q = nearestOnSegment(px, py, a.x, a.y, b.x, b.y);
    if (q.dist <= reach && (!best || q.dist < best.dist)) best = q;
  }
  for (const pc of poolCenters) {
    const d = Math.hypot(px - pc.x, py - pc.y);
    if (d > pc.r + 58) continue;
    const ang = Math.atan2(py - pc.y, px - pc.x);
    const qx = pc.x + Math.cos(ang) * pc.r * 0.88;
    const qy = pc.y + Math.sin(ang) * pc.r * 0.82;
    const edgeDist = Math.abs(d - pc.r * 0.9);
    if (!best || edgeDist < best.dist) best = { x: qx, y: qy, dist: edgeDist };
  }
  return best;
}

function hexToNum(hex?: string): number | undefined {
  if (!hex) return undefined;
  const v = hex.replace('#', '');
  return parseInt(v, 16);
}

function resolveScene(scene: GardenSceneData) {
  const buildings: SceneBuilding[] = scene.buildings.map((b) => {
    const c = logicalToScene(b.logical.x, b.logical.y, scene.width, scene.height);
    return {
      ...b,
      x: b.x ?? c.x - b.w / 2,
      y: b.y ?? c.y - b.h * 0.72,
    };
  });
  const npcs: SceneNpc[] = scene.npcs.map((n) => {
    const p = logicalToScene(n.logical.x, n.logical.y, scene.width, scene.height);
    return {
      ...n,
      x: n.x ?? p.x,
      y: n.y ?? p.y,
    };
  });
  return { buildings, npcs };
}

export default function GardenScene({ scene, pools, bookSlug }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const hostRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const viewRef = useRef<{ x: number; y: number; scale: number } | null>(null);
  const restoreRef = useRef<{ x: number; y: number; scale: number } | null>(null);
  const selectedIdRef = useRef<string | null>(null);
  const tapHandlerRef = useRef<(b: SceneBuilding) => void>(() => {});
  const routeRef = useRef<{ aId: string | null; bId: string | null; label: string } | null>(null);

  const [selected, setSelected] = useState<SceneBuilding | null>(null);
  selectedIdRef.current = selected?.id ?? null;
  const [dialogue, setDialogue] = useState<{ npc: SceneNpc; line: DialogueLine } | null>(null);
  const [sceneReady, setSceneReady] = useState(false);
  const [sceneError, setSceneError] = useState<string | null>(null);
  const [zoneFilter, setZoneFilter] = useState<string>('all');
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [routeMode, setRouteMode] = useState(false);
  const [routeA, setRouteA] = useState<SceneBuilding | null>(null);
  const [routeB, setRouteB] = useState<SceneBuilding | null>(null);

  const graphHeight = 'calc(100dvh - var(--graph-chrome, 10.5rem))';

  const { buildings, npcs } = useMemo(() => resolveScene(scene), [scene]);

  const zones = useMemo(
    () => ['all', ...Array.from(new Set(buildings.map((b) => b.zone))).sort()],
    [buildings],
  );

  const visibleBuildings = useMemo(
    () => (zoneFilter === 'all' ? buildings : buildings.filter((b) => b.zone === zoneFilter)),
    [buildings, zoneFilter],
  );

  const compactLabels = buildings.length >= 20;

  const buildingById = useMemo(
    () => new Map(buildings.map((b) => [b.id, b])),
    [buildings],
  );

  const distancesFrom = useMemo(() => {
    if (!selected) return [];
    return buildings
      .filter((b) => b.id !== selected.id)
      .map((b) => ({
        id: b.id,
        name: b.name,
        steps: logicalSteps(selected.logical, b.logical, scene.px_per_step),
        bearing: bearingLabel(selected.logical, b.logical),
      }))
      .sort((a, b) => a.steps - b.steps);
  }, [selected, buildings, scene.px_per_step]);

  const routeInfo = useMemo(() => {
    if (!routeA || !routeB) return null;
    return {
      steps: logicalSteps(routeA.logical, routeB.logical, scene.px_per_step),
      bearing: bearingLabel(routeA.logical, routeB.logical),
    };
  }, [routeA, routeB, scene.px_per_step]);

  const routeLabel = routeInfo ? `约 ${routeInfo.steps} 步` : '';

  // 点击建筑的行为随模式而变（用 ref 避免重建 Pixi 场景）
  tapHandlerRef.current = (b: SceneBuilding) => {
    setDialogue(null);
    if (routeMode) {
      if (!routeA || (routeA && routeB)) {
        setRouteA(b);
        setRouteB(null);
      } else if (b.id !== routeA.id) {
        setRouteB(b);
      }
    } else {
      setSelected(b);
    }
  };
  routeRef.current = { aId: routeA?.id ?? null, bId: routeB?.id ?? null, label: routeLabel };

  const toggleRoute = () => {
    const next = !routeMode;
    setRouteMode(next);
    setRouteA(null);
    setRouteB(null);
    if (next) setSelected(null);
    const app = appRef.current as (Application & { _reset?: () => void }) | null;
    app?._reset?.(); // 回到整园，便于看两点连线
  };

  const rollDialogue = (npc: SceneNpc) => {
    const pool = pools[npc.id];
    if (!pool || pool.length === 0) return;
    const line = pool[Math.floor(Math.random() * pool.length)];
    setDialogue({ npc, line });
  };

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let disposed = false;
    const app = new Application();

    const cleanups: Array<() => void> = [];

    const waitForHostSize = async (): Promise<boolean> => {
      let attempts = 0;
      while (host.clientWidth < 16 || host.clientHeight < 16) {
        if (disposed) return false;
        attempts += 1;
        if (attempts > 240) {
          setSceneError('实景画布高度为 0，请刷新页面');
          return false;
        }
        await new Promise<void>((r) => requestAnimationFrame(() => r()));
      }
      return true;
    };

    (async () => {
      setSceneError(null);
      setSceneReady(false);
      if (!(await waitForHostSize())) return;

      try {
        await app.init({
          antialias: true,
          backgroundAlpha: 0,
          resizeTo: host,
          resolution: Math.min(window.devicePixelRatio || 1, 2),
          autoDensity: true,
        });
      } catch (err) {
        if (!disposed) {
          setSceneError(err instanceof Error ? err.message : 'Pixi 初始化失败');
        }
        return;
      }
      if (disposed) {
        app.destroy(true);
        return;
      }
      appRef.current = app;
      host.appendChild(app.canvas);
      app.canvas.style.touchAction = 'none';

      try {
      const world = new Container();
      app.stage.addChild(world);

      // 载入写实等距美术资产（sprite + 平铺纹理）
      const assetUrls = Array.from(new Set(Object.values(SCENE_ASSETS)));
      const tex = (await Assets.load(assetUrls)) as Record<string, Texture>;
      if (disposed) return;

      // ============ 沙盘底（按真坐标，北在上，与 /honglou/map 同源）============
      const margin = 26;
      const gX = margin;
      const gY = margin;
      const gW = scene.width - margin * 2;
      const gH = scene.height - margin * 2;

      // 园外暗色林地
      const outer = new Graphics();
      outer.rect(0, 0, scene.width, scene.height).fill({ color: 0x0f1519 });
      outer.roundRect(gX - 18, gY - 18, gW + 36, gH + 36, 30).fill({ color: 0x223524 });
      world.addChild(outer);

      // 园内草地纹理（圆角裁切）
      const grassMask = new Graphics().roundRect(gX, gY, gW, gH, 18).fill({ color: 0xffffff });
      const grass = new TilingSprite({ texture: tex[SCENE_ASSETS.grass], width: gW, height: gH });
      grass.position.set(gX, gY);
      grass.tileScale.set(0.42);
      grass.mask = grassMask;
      world.addChild(grassMask, grass);
      // 暖光叠加 + 内描边
      const grassTone = new Graphics();
      grassTone.roundRect(gX, gY, gW, gH, 18).fill({ color: 0x2f4a2c, alpha: 0.16 });
      grassTone.roundRect(gX, gY, gW, gH, 18).stroke({ width: 1, color: 0xb9c79f, alpha: 0.18 });
      world.addChild(grassTone);

      // 水系：仅沿 seed 水系节点连线成溪（南北中轴说 · 沁芳溪为纲；无中心大池/外部复原图）
      const sceneOf = (id: string) => {
        const n = buildingById.get(id);
        return n ? logicalToScene(n.logical.x, n.logical.y, scene.width, scene.height) : null;
      };
      // 溪流中心线段（第17回园记 + seed 节点：中轴 沁芳亭↔沁芳闸，东出蓼溆·船坞，南入柳叶渚）
      const streamSegs: Array<[string, string]> = [
        ['沁芳亭', '沁芳闸'],
        ['沁芳闸', '柳叶渚'],
        ['沁芳亭', '蓼溆'],
        ['蓼溆', '船坞'],
      ];
      const waterBank = new Graphics();
      const waterShape = new Graphics();
      const STREAM_R = 34;
      const streamLines: Array<[LogicalPoint, LogicalPoint]> = [];
      const poolCenters: Array<{ x: number; y: number; r: number }> = [];
      let waterAvoidPts: LogicalPoint[] = [];
      const stamp = (g: Graphics, a: LogicalPoint, b: LogicalPoint, r: number) => {
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const len = Math.hypot(dx, dy) || 1;
        const nx = (-dy / len) * r;
        const ny = (dx / len) * r;
        g.poly([a.x + nx, a.y + ny, b.x + nx, b.y + ny, b.x - nx, b.y - ny, a.x - nx, a.y - ny]);
        g.circle(a.x, a.y, r);
        g.circle(b.x, b.y, r);
      };
      let waterDrawn = 0;
      let waterReflectCtx: {
        reflectionLayer: Container;
        streamLines: Array<[LogicalPoint, LogicalPoint]>;
        poolCenters: Array<{ x: number; y: number; r: number }>;
        streamR: number;
      } | null = null;
      for (const [from, to] of streamSegs) {
        const a = sceneOf(from);
        const b = sceneOf(to);
        if (!a || !b) continue;
        stamp(waterBank, a, b, STREAM_R + 6);
        stamp(waterShape, a, b, STREAM_R);
        streamLines.push([a, b]);
        waterDrawn += 1;
      }
      // 沁芳亭 / 沁芳闸：节点处略放宽成小潭（非中心大湖）
      for (const id of ['沁芳亭', '沁芳闸']) {
        const p = sceneOf(id);
        if (!p) continue;
        waterBank.circle(p.x, p.y, 46);
        waterShape.circle(p.x, p.y, 40);
        poolCenters.push({ x: p.x, y: p.y, r: 40 });
        waterDrawn += 1;
      }
      if (waterDrawn > 0) {
        waterBank.fill({ color: 0x16322f, alpha: 0.55 });
        waterShape.fill({ color: 0xffffff });

        const waterLayer = new Container();
        const reflectionLayer = new Container(); // 邻水建筑倒影（建筑循环后填充）
        // 黛碧静水（中式园林水色：不饱和青碧，自上而下加深）
        const waterGrad = new FillGradient({
          type: 'linear',
          start: { x: 0, y: 0 },
          end: { x: 0, y: 1 },
          textureSpace: 'local',
          colorStops: [
            { offset: 0, color: 0x6f998e },
            { offset: 0.5, color: 0x3c6b65 },
            { offset: 1, color: 0x244744 },
          ],
        });
        const fillG = new Graphics();
        fillG.rect(gX, gY, gW, gH).fill(waterGrad);
        waterLayer.addChild(fillG, reflectionLayer);

        // 荷叶 sprite（确定性散布，受水域遮罩裁切）
        const plantRnd = mulberry32(0x10a75c0d);
        const padLayer = new Container();
        const lotusPadTex = tex[SCENE_ASSETS.lotusPad];
        const lotusBloomTex = tex[SCENE_ASSETS.lotusBloom];
        const placePadSprite = (x: number, y: number, scale: number) => {
          const bloom = plantRnd() < 0.22;
          const t = bloom ? lotusBloomTex : lotusPadTex;
          if (!t) return;
          const sp = new Sprite(t);
          sp.anchor.set(0.5, 0.55);
          const w = (bloom ? 34 : 30) * scale * (0.85 + plantRnd() * 0.3);
          sp.width = w;
          sp.height = w * (t.height / t.width);
          sp.rotation = (plantRnd() - 0.5) * 0.5;
          sp.position.set(x, y);
          padLayer.addChild(sp);
        };
        poolCenters.forEach((pc) => {
          const n = 3 + Math.floor(plantRnd() * 3);
          for (let i = 0; i < n; i++) {
            const ang = plantRnd() * Math.PI * 2;
            const rr = plantRnd() * (pc.r - 14);
            placePadSprite(pc.x + Math.cos(ang) * rr, pc.y + Math.sin(ang) * rr * 0.7, 1);
          }
        });
        streamLines.forEach(([a, b]) => {
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const len = Math.hypot(dx, dy) || 1;
          const nx = -dy / len;
          const ny = dx / len;
          const n = Math.max(1, Math.floor(len / 100));
          for (let i = 0; i < n; i++) {
            const t = 0.2 + plantRnd() * 0.6;
            const off = (plantRnd() - 0.5) * (STREAM_R - 10) * 2;
            placePadSprite(a.x + dx * t + nx * off, a.y + dy * t + ny * off, 0.85);
          }
        });
        waterLayer.addChild(padLayer);

        // 动态涟漪圈：缓缓扩散后淡出、循环重生（落叶 / 游鱼）
        const ripples = new Graphics();
        waterLayer.addChild(ripples);
        const ripPts: Array<{ x: number; y: number }> = [];
        poolCenters.forEach((pc) => ripPts.push({ x: pc.x, y: pc.y }));
        streamLines.forEach(([a, b]) => ripPts.push({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }));
        type Rip = { x: number; y: number; r: number; max: number };
        const spawnRip = (): Rip => {
          const p = ripPts[Math.floor(plantRnd() * ripPts.length)] ?? { x: gX, y: gY };
          return {
            x: p.x + (plantRnd() - 0.5) * 34,
            y: p.y + (plantRnd() - 0.5) * 22,
            r: 1 + plantRnd() * 6,
            max: 16 + plantRnd() * 20,
          };
        };
        const rips: Rip[] = Array.from({ length: 5 }, spawnRip);
        const drawRipples = () => {
          ripples.clear();
          for (const rp of rips) {
            const a = Math.max(0, 0.34 * (1 - rp.r / rp.max));
            if (a <= 0.01) continue;
            ripples.ellipse(rp.x, rp.y, rp.r, rp.r * 0.6).stroke({ width: 1.4, color: 0xdfeee8, alpha: a });
            if (rp.r > 7) {
              ripples.ellipse(rp.x, rp.y, rp.r * 0.58, rp.r * 0.35).stroke({ width: 1, color: 0xdfeee8, alpha: a * 0.7 });
            }
          }
        };
        drawRipples();
        const onWater = () => {
          const dt = app.ticker.deltaTime;
          for (let i = 0; i < rips.length; i++) {
            rips[i].r += 0.32 * dt;
            if (rips[i].r >= rips[i].max) rips[i] = spawnRip();
          }
          drawRipples();
        };
        app.ticker.add(onWater);
        cleanups.push(() => app.ticker.remove(onWater));

        waterLayer.mask = waterShape;
        world.addChild(waterBank, waterShape, waterLayer);

        // 驳岸假山 sprite + 芦苇：叠石簇框住水缘
        const rockRnd = mulberry32(0x7a31b9c1);
        const rocks = new Container();
        const rockTex = [SCENE_ASSETS.rockA, SCENE_ASSETS.rockB, SCENE_ASSETS.rockC]
          .map((u) => tex[u])
          .filter(Boolean) as Texture[];
        const placeRockery = (x: number, y: number, size = 1) => {
          if (!rockTex.length) return;
          const n = 2 + Math.floor(rockRnd() * 3);
          for (let i = 0; i < n; i++) {
            const rt = rockTex[Math.floor(rockRnd() * rockTex.length)]!;
            const sp = new Sprite(rt);
            sp.anchor.set(0.5, 0.88);
            const w = (16 + rockRnd() * 22) * size;
            sp.width = w;
            sp.height = w * (rt.height / rt.width);
            sp.position.set(x + (rockRnd() - 0.5) * 14, y + (rockRnd() - 0.5) * 8 - i * 4);
            sp.rotation = (rockRnd() - 0.5) * 0.35;
            rocks.addChild(sp);
          }
        };
        const placeReed = (x: number, y: number) => {
          const reedG = new Graphics();
          const n = 3 + Math.floor(rockRnd() * 3);
          for (let i = 0; i < n; i++) {
            const sway = (rockRnd() - 0.5) * 0.6;
            const h = 9 + rockRnd() * 11;
            const bx = x + (i - n / 2) * 1.8;
            reedG.moveTo(bx, y).lineTo(bx + Math.sin(sway) * h, y - h);
          }
          reedG.stroke({ width: 1.4, color: 0x5f7d3a, alpha: 0.8 });
          rocks.addChild(reedG);
        };
        streamLines.forEach(([a, b]) => {
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const len = Math.hypot(dx, dy) || 1;
          const ux = dx / len;
          const uy = dy / len;
          const nx = -uy;
          const ny = ux;
          for (let d = 0; d <= len; d += 22) {
            for (const side of [-1, 1]) {
              const roll = rockRnd();
              if (roll < 0.32) continue;
              const off = (STREAM_R + 3) * side + (rockRnd() - 0.5) * 5;
              const x = a.x + ux * d + nx * off;
              const y = a.y + uy * d + ny * off;
              if (roll > 0.88) placeReed(x, y);
              else if (roll > 0.55) placeRockery(x, y, 0.75);
              else placeRockery(x, y, 1);
            }
          }
        });
        poolCenters.forEach((pc) => {
          const n = 12;
          for (let i = 0; i < n; i++) {
            const roll = rockRnd();
            if (roll < 0.22) continue;
            const ang = (i / n) * Math.PI * 2 + (rockRnd() - 0.5) * 0.3;
            const x = pc.x + Math.cos(ang) * (pc.r + 4);
            const y = pc.y + Math.sin(ang) * (pc.r + 4) * 0.82;
            if (roll > 0.92) placeReed(x, y);
            else placeRockery(x, y, 1.05);
          }
        });
        world.addChild(rocks);

        waterReflectCtx = {
          reflectionLayer,
          streamLines,
          poolCenters,
          streamR: STREAM_R,
        };
        waterAvoidPts = [
          ...poolCenters.map((pc) => ({ x: pc.x, y: pc.y })),
          ...streamLines.map(([a, b]) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 })),
        ];
      }

      // 园墙（双线）
      const wall = new Graphics();
      wall.roundRect(gX, gY, gW, gH, 18).stroke({ width: 7, color: 0x6b5f54 });
      wall.roundRect(gX, gY, gW, gH, 18).stroke({ width: 2, color: 0x9c8e7d, alpha: 0.7 });
      world.addChild(wall);

      // 园路网：浅色石径连通各院落（呼应美术画廊的步道感），置于林木/建筑之下
      const pathPts: LogicalPoint[] = [];
      {
        const pn = visibleBuildings.map((b) =>
          logicalToScene(b.logical.x, b.logical.y, scene.width, scene.height),
        );
        const dist2 = (i: number, j: number) =>
          (pn[i].x - pn[j].x) ** 2 + (pn[i].y - pn[j].y) ** 2;
        const edgeKeys = new Set<string>();
        const edges: Array<[number, number]> = [];
        const addEdge = (i: number, j: number) => {
          if (i === j) return;
          const k = i < j ? `${i}-${j}` : `${j}-${i}`;
          if (!edgeKeys.has(k)) {
            edgeKeys.add(k);
            edges.push([i, j]);
          }
        };
        if (pn.length > 1) {
          // 最小生成树（Prim）：每处院落都连通
          const inTree = new Array(pn.length).fill(false);
          inTree[0] = true;
          for (let c = 1; c < pn.length; c++) {
            let bi = -1, bj = -1, bd = Infinity;
            for (let i = 0; i < pn.length; i++) {
              if (!inTree[i]) continue;
              for (let j = 0; j < pn.length; j++) {
                if (inTree[j]) continue;
                const d = dist2(i, j);
                if (d < bd) { bd = d; bi = i; bj = j; }
              }
            }
            if (bj < 0) break;
            inTree[bj] = true;
            addEdge(bi, bj);
          }
          // 近邻补边：制造少量环路，更像园林而非纯树状
          for (let i = 0; i < pn.length; i++) {
            let nj = -1, nd = Infinity;
            for (let j = 0; j < pn.length; j++) {
              if (j === i) continue;
              const d = dist2(i, j);
              if (d < nd) { nd = d; nj = j; }
            }
            if (nj >= 0) addEdge(i, nj);
          }
        }
        // 南门入口主路：园墙底部正中 → 最近院落
        const gate = { x: gX + gW / 2, y: gY + gH };
        let gi = -1, gdist = Infinity;
        pn.forEach((p, i) => {
          const d = (p.x - gate.x) ** 2 + (p.y - gate.y) ** 2;
          if (d < gdist) { gdist = d; gi = i; }
        });

        const prnd = mulberry32(0x9e3779b1);
        const segs: Array<{ a: LogicalPoint; c: LogicalPoint; b: LogicalPoint }> = [];
        const pushSeg = (a: LogicalPoint, b: LogicalPoint, wind = 1) => {
          const dx = b.x - a.x, dy = b.y - a.y;
          const len = Math.hypot(dx, dy) || 1;
          const off = (prnd() - 0.5) * Math.min(len * 0.16, 46) * wind;
          const c = {
            x: (a.x + b.x) / 2 + (-dy / len) * off,
            y: (a.y + b.y) / 2 + (dx / len) * off,
          };
          segs.push({ a, c, b });
          for (let t = 0; t <= 1.001; t += 0.25) {
            const it = 1 - t;
            pathPts.push({
              x: it * it * a.x + 2 * it * t * c.x + t * t * b.x,
              y: it * it * a.y + 2 * it * t * c.y + t * t * b.y,
            });
          }
        };
        edges.forEach(([i, j]) => pushSeg(pn[i], pn[j]));
        if (gi >= 0) pushSeg(gate, pn[gi], 0.35);

        if (segs.length) {
          // 落地软影（在石板之下，给路面接地感）
          const sh = new Graphics();
          segs.forEach((s) => sh.moveTo(s.a.x, s.a.y).quadraticCurveTo(s.c.x, s.c.y, s.b.x, s.b.y));
          sh.stroke({ width: 22, color: 0x2c2a1e, alpha: 0.15, cap: 'round', join: 'round' });
          world.addChild(sh);

          // 青石板分块铺面：沿曲线按弧长铺石板（带缝、逐块色差）
          const SLAB_W = 15;
          const SLAB_LEN = 15;
          const SLAB_GAP = 4.5;
          const slabRnd = mulberry32(0x5eed51ab);
          const slabG = new Graphics();
          const drawSlabs = (a: LogicalPoint, c: LogicalPoint, b: LogicalPoint) => {
            const N = Math.max(10, Math.ceil((Math.hypot(b.x - a.x, b.y - a.y) + 40) / 8));
            const pts: LogicalPoint[] = [];
            for (let i = 0; i <= N; i++) {
              const t = i / N;
              const it = 1 - t;
              pts.push({
                x: it * it * a.x + 2 * it * t * c.x + t * t * b.x,
                y: it * it * a.y + 2 * it * t * c.y + t * t * b.y,
              });
            }
            let acc = 0;
            let nextAt = SLAB_LEN / 2;
            for (let i = 1; i < pts.length; i++) {
              const p0 = pts[i - 1];
              const p1 = pts[i];
              const segLen = Math.hypot(p1.x - p0.x, p1.y - p0.y) || 1e-3;
              while (nextAt <= acc + segLen) {
                const f = (nextAt - acc) / segLen;
                const cx = p0.x + (p1.x - p0.x) * f;
                const cy = p0.y + (p1.y - p0.y) * f;
                const ux = (p1.x - p0.x) / segLen;
                const uy = (p1.y - p0.y) / segLen;
                const nx = -uy;
                const ny = ux;
                const hl = SLAB_LEN / 2;
                const hw = SLAB_W / 2;
                const corners = [
                  cx - ux * hl - nx * hw, cy - uy * hl - ny * hw,
                  cx + ux * hl - nx * hw, cy + uy * hl - ny * hw,
                  cx + ux * hl + nx * hw, cy + uy * hl + ny * hw,
                  cx - ux * hl + nx * hw, cy - uy * hl + ny * hw,
                ];
                const j = Math.floor((slabRnd() - 0.5) * 26);
                const r = Math.max(70, Math.min(165, 0x83 + j));
                const g = Math.max(78, Math.min(175, 0x90 + j));
                const bl = Math.max(78, Math.min(175, 0x90 + j));
                slabG
                  .poly(corners)
                  .fill({ color: (r << 16) | (g << 8) | bl, alpha: 0.96 })
                  .stroke({ width: 1.1, color: 0x434d4c, alpha: 0.6 });
                nextAt += SLAB_LEN + SLAB_GAP;
              }
              acc += segLen;
            }
          };
          segs.forEach((s) => drawSlabs(s.a, s.c, s.b));
          world.addChild(slabG);
        }
        if (gi >= 0) {
          const apron = new Graphics();
          apron.roundRect(gate.x - 28, gate.y - 12, 56, 24, 5).fill({ color: 0x434d4c, alpha: 0.6 });
          apron.roundRect(gate.x - 25, gate.y - 10, 50, 20, 4).fill({ color: 0x8b9795, alpha: 0.96 });
          apron
            .moveTo(gate.x - 8, gate.y - 10)
            .lineTo(gate.x - 8, gate.y + 10)
            .moveTo(gate.x + 9, gate.y - 10)
            .lineTo(gate.x + 9, gate.y + 10)
            .stroke({ width: 1.2, color: 0x434d4c, alpha: 0.6 });
          world.addChild(apron);
        }
      }

      // 第17回游线（金色淡线，叠在石径之上）
      if (scene.paths.length) {
        const tline = new Graphics();
        scene.paths.forEach((p) => {
          const a = sceneOf(p.from);
          const b = sceneOf(p.to);
          if (!a || !b) return;
          tline.moveTo(a.x, a.y).lineTo(b.x, b.y);
        });
        tline.stroke({ width: 2.5, color: 0xe7c873, alpha: 0.4 });
        world.addChild(tline);
      }

      // ============ 林木 + 建筑：按 baseY 统一深度排序 ============
      const labelSize = compactLabels ? 13 : 17;
      const drawables: Array<{ baseY: number; node: Container }> = [];
      // 建筑句柄索引：选中态不重建场景，只在此基础上切换高亮 + 移动相机
      const nodeIndex = new Map<
        string,
        { node: Container; gx: number; gy: number; w: number; h: number; setLabelSel: (on: boolean) => void }
      >();
      const selectionRing = new Graphics();
      const routeLayer = new Container(); // 动线连线 + 步数（置最顶）
      const labelLayer = new Container();

      // 林木散点（确定性；避开建筑、水面与园路）
      const rnd = mulberry32(20260616);
      const treeTex = tex[SCENE_ASSETS.trees];
      const treeRatio = treeTex.height / treeTex.width;
      let placed = 0;
      for (let i = 0; i < 1500 && placed < 190; i++) {
        const tx = gX + 24 + rnd() * (gW - 48);
        const ty = gY + 24 + rnd() * (gH - 48);
        const nearBuilding = buildings.some(
          (b) => Math.hypot(center(b).x - tx, center(b).y - ty) < 64,
        );
        const nearWater = waterAvoidPts.some((p) => Math.hypot(p.x - tx, p.y - ty) < 62);
        const nearPath = pathPts.some((p) => Math.hypot(p.x - tx, p.y - ty) < 28);
        if (nearBuilding || nearWater || nearPath) continue;
        const tw = 56 + rnd() * 48;
        const sp = new Sprite(treeTex);
        sp.anchor.set(0.5, 0.86);
        sp.width = tw;
        sp.height = tw * treeRatio;
        sp.position.set(tx, ty);
        const node = new Container();
        node.addChild(sp);
        drawables.push({ baseY: ty, node });
        placed++;
      }

      // 建筑（真坐标摆等距 sprite）
      for (const b of visibleBuildings) {
        const ground = logicalToScene(b.logical.x, b.logical.y, scene.width, scene.height);
        const node = new Container();
        node.eventMode = 'static';
        node.cursor = 'pointer';
        node.position.set(ground.x, ground.y);

        const archTex = tex[SCENE_ASSETS[archetypeFor(b)]];
        const dispW = b.w * 1.05;
        const dispH = archTex ? dispW * (archTex.height / archTex.width) : b.h;

        // 程序化接地软投影（sprite 已去掉烘焙阴影）
        const shadow = new Graphics();
        shadow.ellipse(dispW * 0.05, 0, dispW * 0.38, dispW * 0.12).fill({ color: 0x0a0f0a, alpha: 0.26 });
        node.addChild(shadow);

        if (archTex) {
          const sp = new Sprite(archTex);
          sp.anchor.set(0.5, 0.9);
          sp.width = dispW;
          sp.height = dispH;
          node.addChild(sp);
        } else {
          const g = new Graphics();
          g.roundRect(-b.w / 2, -b.h, b.w, b.h, 6).fill({ color: ZONE_FILL[b.zone] ?? 0x8a6f4a });
          node.addChild(g);
        }
        node.hitArea = new Rectangle(-dispW / 2, -dispH * 0.9, dispW, dispH);

        node.on('pointertap', () => tapHandlerRef.current?.(b));
        drawables.push({ baseY: ground.y, node });

        // 名称标签（统一置顶层，避免被南侧建筑遮挡）
        const nameText = new Text({
          text: b.name,
          style: {
            fontFamily: 'Noto Serif SC, serif',
            fontSize: labelSize,
            fill: 0xfdf6e3,
            fontWeight: 600,
          },
        });
        nameText.anchor.set(0.5, 0);
        const nameBg = new Graphics();
        const drawLabelBg = (on: boolean) => {
          nameBg
            .clear()
            .roundRect(-nameText.width / 2 - 8, -3, nameText.width + 16, nameText.height + 6, 5)
            .fill({ color: on ? 0x1a120d : 0x16110e, alpha: on ? 0.8 : 0.52 })
            .stroke({ width: 1, color: 0xc5b08f, alpha: on ? 0.65 : 0.3 });
        };
        drawLabelBg(false);
        const nameTag = new Container();
        nameTag.addChild(nameBg, nameText);
        nameTag.position.set(ground.x, ground.y + 8);
        labelLayer.addChild(nameTag);

        nodeIndex.set(b.id, {
          node,
          gx: ground.x,
          gy: ground.y,
          w: b.w,
          h: b.h,
          setLabelSel: (on: boolean) => {
            nameText.style.fill = on ? 0xf4d796 : 0xfdf6e3;
            nameText.style.fontWeight = on ? 700 : 600;
            drawLabelBg(on);
          },
        });
      }

      // 邻水建筑极淡倒影：邻近 sprite 压扁翻转，半透明画入水面层
      if (waterReflectCtx) {
        const { reflectionLayer, streamLines, poolCenters, streamR } = waterReflectCtx;
        for (const b of visibleBuildings) {
          if (b.zone === '水系' || b.zone === '路径') continue;
          const ground = logicalToScene(b.logical.x, b.logical.y, scene.width, scene.height);
          const wp = nearestWaterPoint(ground.x, ground.y, streamLines, poolCenters, streamR);
          if (!wp || wp.dist > 68 || wp.dist < 6) continue;
          const archTex = tex[SCENE_ASSETS[archetypeFor(b)]];
          if (!archTex) continue;
          const dispW = b.w * 1.05;
          const baseScale = dispW / archTex.width;
          const refl = new Sprite(archTex);
          refl.anchor.set(0.5, 0);
          refl.scale.set(baseScale * 0.88, -baseScale * 0.24);
          refl.position.set(wp.x + (ground.x - wp.x) * 0.22, wp.y + 3);
          refl.alpha = 0.1 + (1 - wp.dist / 68) * 0.07;
          refl.tint = 0x7a9894;
          reflectionLayer.addChild(refl);
        }
      }

      drawables.sort((a, b) => a.baseY - b.baseY);
      for (const d of drawables) world.addChild(d.node);
      world.addChild(labelLayer);
      world.addChild(routeLayer);

      // ---- NPC ----
      for (const n of npcs) {
        const node = new Container();
        node.position.set(n.x, n.y);
        node.eventMode = 'static';
        node.cursor = 'pointer';

        const tint = hexToNum(n.tint) ?? 0xe0b059;
        const fig = new Graphics();
        // 光晕
        fig.circle(0, 0, 30).fill({ color: tint, alpha: 0.18 });
        // 身体
        fig.roundRect(-15, -6, 30, 40, 12).fill({ color: tint, alpha: 0.92 });
        // 头
        fig.circle(0, -18, 13).fill({ color: 0xf3e2cf });
        fig.circle(0, -18, 13).stroke({ width: 2, color: tint });
        node.addChild(fig);

        const tag = new Text({
          text: n.name,
          style: {
            fontFamily: 'Noto Serif SC, serif',
            fontSize: 16,
            fill: 0xffffff,
            fontWeight: '700',
          },
        });
        tag.anchor.set(0.5, 0);
        const tagBg = new Graphics();
        tagBg
          .roundRect(-tag.width / 2 - 8, 40, tag.width + 16, tag.height + 6, 6)
          .fill({ color: 0x0a0608, alpha: 0.78 });
        const tagText = tag;
        tagText.position.set(0, 43);
        node.addChild(tagBg, tagText);

        if (n.sprite) {
          Assets.load(n.sprite)
            .then((tex: Texture) => {
              if (disposed) return;
              const sp = new Sprite(tex);
              const ratio = tex.height / tex.width;
              sp.anchor.set(0.5, 1);
              sp.width = 104;
              sp.height = 104 * ratio;
              node.removeChild(fig);
              node.addChildAt(sp, 0);
            })
            .catch(() => {
              /* 占位人物保留 */
            });
        }

        node.on('pointertap', () => {
          setSelected(null);
          rollDialogue(n);
        });
        world.addChild(node);
      }

      // ---- 相机：对焦/缩放/平移 + 补间（选中态不重建场景） ----
      let focusPoint: { x: number; y: number } | null = null;
      const MIN_SCALE = 0.16;
      const MAX_SCALE = 4;
      const clampScale = (v: number) => Math.max(MIN_SCALE, Math.min(MAX_SCALE, v));
      const baseFitScale = () =>
        Math.min(app.screen.width / scene.width, app.screen.height / scene.height) * 0.94;
      type View = { x: number; y: number; scale: number };
      const currentView = (): View => ({ x: world.x, y: world.y, scale: world.scale.x });
      const applyView = (v: View) => {
        world.scale.set(v.scale);
        world.position.set(v.x, v.y);
        viewRef.current = v;
      };
      // 手动平移/缩放后：既更新相机，又把它记为「关闭后回退」目标
      const saveView = () => {
        const v = currentView();
        viewRef.current = v;
        restoreRef.current = v;
      };
      const defaultView = (): View => {
        const sw = app.screen.width;
        const sh = app.screen.height;
        const s = baseFitScale();
        return { x: (sw - scene.width * s) / 2, y: (sh - scene.height * s) / 2, scale: s };
      };
      const focusView = (): View => {
        const sw = app.screen.width;
        const sh = app.screen.height;
        const s = clampScale(baseFitScale() * 2.6);
        // 略偏左，避免被右侧详情面板遮住
        return { x: sw * 0.42 - focusPoint!.x * s, y: sh * 0.46 - focusPoint!.y * s, scale: s };
      };
      const targetView = (): View => (focusPoint ? focusView() : restoreRef.current ?? defaultView());

      // ---- 相机补间 ----
      let tweenRaf = 0;
      const cancelTween = () => {
        if (tweenRaf) cancelAnimationFrame(tweenRaf);
        tweenRaf = 0;
      };
      cleanups.push(cancelTween);
      const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
      const TWEEN_MS = 460;
      const tweenView = (from: View, to: View) => {
        cancelTween();
        if (Math.abs(from.x - to.x) < 1 && Math.abs(from.y - to.y) < 1 && Math.abs(from.scale - to.scale) < 0.001) {
          applyView(to);
          return;
        }
        applyView(from);
        const start = performance.now();
        const step = (now: number) => {
          const t = Math.min(1, (now - start) / TWEEN_MS);
          const k = easeOutCubic(t);
          applyView({
            x: from.x + (to.x - from.x) * k,
            y: from.y + (to.y - from.y) * k,
            // 缩放用几何插值，过渡更自然
            scale: from.scale * Math.pow(to.scale / from.scale, k),
          });
          if (t < 1) tweenRaf = requestAnimationFrame(step);
          else tweenRaf = 0;
        };
        tweenRaf = requestAnimationFrame(step);
      };

      const updateHitArea = () => {
        app.stage.hitArea = new Rectangle(0, 0, app.screen.width, app.screen.height);
      };
      // 尺寸/初始：即时贴合，不打断已有补间逻辑
      const reflow = () => {
        updateHitArea();
        cancelTween();
        applyView(targetView());
      };

      // 选中态切换：只换高亮 + 移动相机，绝不重建场景（消除闪烁）
      let selectedId: string | null = null;
      const setSelection = (id: string | null, animate: boolean) => {
        if (selectedId && selectedId !== id) nodeIndex.get(selectedId)?.setLabelSel(false);
        if (selectionRing.parent) selectionRing.parent.removeChild(selectionRing);
        selectedId = id;
        const cur = id ? nodeIndex.get(id) : undefined;
        if (cur) {
          cur.setLabelSel(true);
          selectionRing
            .clear()
            .ellipse(0, 0, cur.w * 0.6, cur.h * 0.34)
            .fill({ color: 0xf4d796, alpha: 0.16 })
            .ellipse(0, 0, cur.w * 0.6, cur.h * 0.34)
            .stroke({ width: 2.5, color: 0xf4d796, alpha: 0.85 });
          cur.node.addChildAt(selectionRing, 1); // 影子之上、建筑之下
          focusPoint = { x: cur.gx, y: cur.gy };
        } else {
          focusPoint = null;
        }
        if (animate) tweenView(currentView(), targetView());
        else reflow();
      };

      app.stage.eventMode = 'static';
      let dragging = false;
      let startP = { x: 0, y: 0 };
      let origin = { x: 0, y: 0 };
      app.stage.on('pointerdown', (e) => {
        dragging = true;
        focusPoint = null; // 手动平移后不再强制对焦（保留选中高亮）
        cancelTween();
        startP = { x: e.global.x, y: e.global.y };
        origin = { x: world.x, y: world.y };
      });
      const endDrag = () => {
        if (dragging) saveView();
        dragging = false;
      };
      app.stage.on('pointerup', endDrag);
      app.stage.on('pointerupoutside', endDrag);
      app.stage.on('pointermove', (e) => {
        if (!dragging) return;
        world.x = origin.x + (e.global.x - startP.x);
        world.y = origin.y + (e.global.y - startP.y);
      });

      const zoomAround = (factor: number, px: number, py: number) => {
        focusPoint = null;
        cancelTween();
        const wx = (px - world.x) / world.scale.x;
        const wy = (py - world.y) / world.scale.y;
        const next = clampScale(world.scale.x * factor);
        world.scale.set(next);
        world.x = px - wx * next;
        world.y = py - wy * next;
        saveView();
      };

      const onWheel = (e: WheelEvent) => {
        e.preventDefault();
        const rect = app.canvas.getBoundingClientRect();
        zoomAround(e.deltaY < 0 ? 1.12 : 0.89, e.clientX - rect.left, e.clientY - rect.top);
      };
      app.canvas.addEventListener('wheel', onWheel, { passive: false });
      cleanups.push(() => app.canvas.removeEventListener('wheel', onWheel));

      let lastW = host.clientWidth;
      let lastH = host.clientHeight;
      const onResize = () => reflow();
      window.addEventListener('resize', onResize);
      window.addEventListener('graph-chrome-sync', onResize);
      cleanups.push(() => {
        window.removeEventListener('resize', onResize);
        window.removeEventListener('graph-chrome-sync', onResize);
      });

      const ro = new ResizeObserver(() => {
        // 仅在尺寸真正变化时重排，避免 observe 的首帧回调打断对焦补间
        const w = host.clientWidth;
        const h = host.clientHeight;
        if (Math.abs(w - lastW) < 2 && Math.abs(h - lastH) < 2) return;
        lastW = w;
        lastH = h;
        reflow();
      });
      ro.observe(host);
      cleanups.push(() => ro.disconnect());

      // 动线连线：A→B 一条金线 + 端点标记 + 中点步数 chip（世界坐标，随缩放自适应）
      const drawRoute = (aId: string | null, bId: string | null, label: string) => {
        routeLayer.removeChildren();
        const A = aId ? nodeIndex.get(aId) : undefined;
        const B = bId ? nodeIndex.get(bId) : undefined;
        if (A) {
          const ma = new Graphics();
          ma.circle(A.gx, A.gy, 9).fill({ color: 0xf4d796, alpha: 0.95 });
          ma.circle(A.gx, A.gy, 15).stroke({ width: 3, color: 0xf4d796, alpha: 0.6 });
          routeLayer.addChild(ma);
        }
        if (A && B) {
          const line = new Graphics();
          line.moveTo(A.gx, A.gy).lineTo(B.gx, B.gy).stroke({ width: 5, color: 0xf4d796, alpha: 0.9 });
          line.circle(B.gx, B.gy, 9).fill({ color: 0xffe9b0, alpha: 0.98 });
          line.circle(B.gx, B.gy, 15).stroke({ width: 3, color: 0xffe9b0, alpha: 0.6 });
          routeLayer.addChild(line);
          if (label) {
            const t = new Text({
              text: label,
              style: { fontFamily: 'Noto Serif SC, serif', fontSize: 18, fill: 0x231708, fontWeight: '700' },
            });
            t.anchor.set(0.5);
            const bg = new Graphics();
            bg
              .roundRect(-t.width / 2 - 11, -t.height / 2 - 6, t.width + 22, t.height + 12, 9)
              .fill({ color: 0xf4d796, alpha: 0.96 })
              .stroke({ width: 1.5, color: 0x6b4f1d, alpha: 0.85 });
            const chip = new Container();
            chip.addChild(bg, t);
            chip.position.set((A.gx + B.gx) / 2, (A.gy + B.gy) / 2);
            routeLayer.addChild(chip);
          }
        }
      };

      // 初始：恢复当前选中态与动线（重建场景如分区切换时也照此对齐），不动画
      setSelection(selectedIdRef.current, false);
      drawRoute(routeRef.current?.aId ?? null, routeRef.current?.bId ?? null, routeRef.current?.label ?? '');
      setSceneReady(true);

      // 暴露给工具栏 / 选中 / 动线副作用
      const ctl = app as unknown as {
        _reset?: () => void;
        _zoom?: (factor: number) => void;
        _select?: (id: string | null) => void;
        _route?: (a: string | null, b: string | null, label: string) => void;
      };
      ctl._select = (id: string | null) => setSelection(id, true);
      ctl._reset = () => {
        restoreRef.current = null;
        setSelection(null, true);
      };
      ctl._zoom = (factor: number) =>
        zoomAround(factor, app.screen.width / 2, app.screen.height / 2);
      ctl._route = drawRoute;
      } catch (e) {
        if (!disposed) {
          setSceneError(e instanceof Error ? e.message : '沙盘渲染失败');
        }
      }
    })();

    return () => {
      disposed = true;
      setSceneReady(false);
      cleanups.forEach((fn) => fn());
      if (appRef.current) {
        appRef.current.destroy(true, { children: true });
        appRef.current = null;
      }
    };
  }, [scene, visibleBuildings, npcs, buildingById, compactLabels]);

  // 选中态变化：不重建场景，仅切换高亮 + 补间相机
  useEffect(() => {
    const app = appRef.current as (Application & { _select?: (id: string | null) => void }) | null;
    app?._select?.(selected?.id ?? null);
  }, [selected?.id]);

  // 动线变化：不重建场景，仅在 routeLayer 重绘连线 + 步数
  useEffect(() => {
    const app = appRef.current as
      | (Application & { _route?: (a: string | null, b: string | null, label: string) => void })
      | null;
    app?._route?.(routeA?.id ?? null, routeB?.id ?? null, routeLabel);
  }, [routeA?.id, routeB?.id, routeLabel]);

  // Esc：按层级收起画廊 / 动线 / 详情 / 对白
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      if (galleryOpen) setGalleryOpen(false);
      else if (routeMode) {
        setRouteMode(false);
        setRouteA(null);
        setRouteB(null);
      } else if (selected) setSelected(null);
      else if (dialogue) setDialogue(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [galleryOpen, routeMode, selected, dialogue]);

  const resetView = () => {
    setSelected(null);
    const app = appRef.current as (Application & { _reset?: () => void }) | null;
    app?._reset?.();
  };

  const zoomView = (factor: number) => {
    const app = appRef.current as (Application & { _zoom?: (f: number) => void }) | null;
    app?._zoom?.(factor);
  };

  const selectedSprite = selected ? SCENE_ASSETS[archetypeFor(selected)] : null;

  return (
    <div
      className="garden-scene graph-explorer relative overflow-hidden"
      style={{ background: gt.backdrop, height: graphHeight, minHeight: graphHeight }}
    >
      <div ref={hostRef} className="absolute inset-0" />

      {!sceneReady && !sceneError && (
        <div className="pointer-events-none absolute inset-0 z-[5] flex items-center justify-center">
          <p className="rounded-lg border border-white/10 bg-slate-900/80 px-4 py-2 text-sm text-slate-300">
            加载大观园2.5D…
          </p>
        </div>
      )}

      {sceneError && (
        <div className="absolute inset-0 z-[5] flex items-center justify-center p-4">
          <p className="max-w-md rounded-xl border border-red-500/30 bg-slate-900/90 px-4 py-3 text-center text-sm text-red-200">
            {sceneError}
          </p>
        </div>
      )}

      {/* 顶栏信息 */}
      <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-md rounded-xl border border-white/10 bg-slate-900/80 p-3 backdrop-blur-md">
        <div className="text-lg font-bold" style={{ color: gt.accentSoft }}>
          {scene.title}
        </div>
        {scene.subtitle && (
          <div className="mt-0.5 text-sm font-medium text-slate-300">{scene.subtitle}</div>
        )}
        <div className="mt-1.5 text-xs leading-relaxed text-amber-100/85">{GARDEN_LAYOUT_DISCLAIMER}</div>
        {scene.scale_note && scene.scale_note !== GARDEN_LAYOUT_DISCLAIMER && (
          <div className="mt-1 text-xs leading-relaxed text-slate-500">{scene.scale_note}</div>
        )}
        <div className="mt-1.5 text-xs text-slate-500">
          点建筑放大看详情 · 点人物随机说一句 · 动线量两点距离 · 滚轮/＋−缩放 · 拖拽平移 · Esc 收起
        </div>
        {bookSlug === 'honglou' && (
          <div className="pointer-events-auto mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs font-medium">
            <a
              href="/honglou/map"
              className="underline decoration-dotted underline-offset-2"
              style={{ color: gt.accentSoft }}
            >
              对照 2D 地图 →
            </a>
          </div>
        )}
      </div>

      <div className="absolute right-3 top-3 z-10 flex flex-wrap items-center justify-end gap-2">
        {zones.length > 2 && (
          <label className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-slate-900/80 px-2.5 py-2 text-sm backdrop-blur-sm">
            <span className="text-slate-400">分区</span>
            <select
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="cursor-pointer bg-transparent font-medium text-slate-200 outline-none"
            >
              {zones.map((z) => (
                <option key={z} value={z} className="bg-slate-900">
                  {z === 'all' ? '全部' : z}
                </option>
              ))}
            </select>
          </label>
        )}
        {scene.gallery && (
          <button
            type="button"
            onClick={() => setGalleryOpen(true)}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/25 hover:text-white"
          >
            美术画廊
          </button>
        )}
        <button
          type="button"
          onClick={toggleRoute}
          aria-pressed={routeMode}
          className={`rounded-lg border px-3.5 py-2 text-sm font-medium backdrop-blur-sm ${
            routeMode
              ? 'border-amber-300/70 bg-amber-300/15 text-amber-100'
              : 'border-white/10 bg-slate-900/80 text-slate-200 hover:border-white/25 hover:text-white'
          }`}
        >
          动线{routeMode ? ' · 开' : ''}
        </button>
        <div className="flex items-center overflow-hidden rounded-lg border border-white/10 bg-slate-900/80 backdrop-blur-sm">
          <button
            type="button"
            onClick={() => zoomView(0.8)}
            aria-label="缩小"
            className="px-3 py-2 text-base font-semibold text-slate-200 hover:bg-white/10 hover:text-white"
          >
            −
          </button>
          <span className="px-1 text-xs text-slate-500">缩放</span>
          <button
            type="button"
            onClick={() => zoomView(1.25)}
            aria-label="放大"
            className="px-3 py-2 text-base font-semibold text-slate-200 hover:bg-white/10 hover:text-white"
          >
            ＋
          </button>
        </div>
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/25 hover:text-white"
        >
          重置视图
        </button>
      </div>

      {/* 动线提示 / 结果条 */}
      {routeMode && (
        <div className="absolute left-1/2 top-16 z-10 -translate-x-1/2 rounded-xl border border-amber-300/40 bg-slate-900/92 px-4 py-2.5 text-center shadow-xl backdrop-blur-md">
          {!routeA ? (
            <span className="text-sm text-slate-200">动线模式 · 点选第一处建筑</span>
          ) : !routeB ? (
            <span className="text-sm text-slate-200">
              起点 <b style={{ color: gt.accentSoft }}>{routeA.name}</b> · 再点选第二处建筑
            </span>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-sm">
                <b style={{ color: gt.accentSoft }}>{routeA.name}</b>
                <span className="mx-1.5 text-amber-200">→</span>
                <b style={{ color: gt.accentSoft }}>{routeB.name}</b>
                <span className="ml-2 text-slate-300">
                  {routeInfo?.bearing} · 约 {routeInfo?.steps} 步
                </span>
              </span>
              <button
                type="button"
                onClick={() => {
                  setRouteA(null);
                  setRouteB(null);
                }}
                className="rounded border border-white/15 px-2 py-0.5 text-xs text-slate-300 hover:border-white/30 hover:text-white"
              >
                重选
              </button>
            </div>
          )}
        </div>
      )}

      {/* 建筑详情 */}
      {!routeMode && selected && (
        <aside
          className="absolute right-3 top-16 z-10 w-72 rounded-xl border bg-slate-900/90 p-4 shadow-xl backdrop-blur-md"
          style={{ borderColor: gt.accentLine }}
        >
          <div className="mb-1 flex items-baseline justify-between">
            <span className="text-xl font-bold" style={{ color: gt.accentSoft }}>
              {selected.name}
            </span>
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="text-sm text-slate-400 hover:text-white"
            >
              关闭
            </button>
          </div>
          {selectedSprite && (
            <div className="mb-2 flex items-end justify-center overflow-hidden rounded-lg border border-white/5 bg-gradient-to-b from-emerald-900/25 via-slate-800/30 to-slate-950/60 pt-2">
              <img
                key={selectedSprite}
                src={selectedSprite}
                alt={`${selected.name} 等距立绘`}
                loading="lazy"
                className="h-24 w-auto object-contain drop-shadow-[0_8px_10px_rgba(0,0,0,0.55)]"
              />
            </div>
          )}
          {selected.plaque && (
            <div className="mb-1 text-sm font-medium" style={{ color: gt.accentSoft }}>
              匾 · {selected.plaque}
            </div>
          )}
          <div className="mb-2 text-xs text-slate-400">{selected.zone}</div>
          {selected.note && (
            <p className="mb-3 text-sm leading-relaxed text-slate-200">{selected.note}</p>
          )}
          <div className="mb-1.5 text-sm font-semibold text-slate-400">到其他建筑（与地图同源）</div>
          <ul className="mb-3 flex flex-col gap-1">
            {distancesFrom.map((d) => (
              <li key={d.id} className="flex justify-between gap-2 text-sm text-slate-200">
                <span>
                  {d.name}
                  <span className="ml-1 text-xs text-slate-500">{d.bearing}</span>
                </span>
                <span style={{ color: gt.accentSoft }}>约 {d.steps} 步</span>
              </li>
            ))}
          </ul>
          {selected.link && (
            <a
              href={selected.link}
              className="flex items-center justify-center rounded-lg border px-3 py-2 text-sm font-semibold transition-colors hover:bg-white/10"
              style={{
                borderColor: gt.accentLine,
                backgroundColor: 'rgba(255,255,255,0.06)',
                color: gt.accentSoft,
              }}
            >
              进入词条页 →
            </a>
          )}
        </aside>
      )}

      {/* 方位罗盘（北在上，与 ECharts 大观园地图一致） */}
      <div
        className="pointer-events-none absolute bottom-4 right-4 z-10 flex flex-col items-center"
        aria-label="方位：北在上"
      >
        <div
          className="relative flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-full border backdrop-blur-sm"
          style={{ borderColor: gt.accentLine, backgroundColor: 'rgba(10,6,8,0.82)' }}
        >
          <span
            className="absolute left-1/2 top-1 -translate-x-1/2 text-sm font-bold"
            style={{ color: gt.accentSoft }}
          >
            北
          </span>
          <span className="absolute bottom-1 left-1/2 -translate-x-1/2 text-xs text-slate-400">南</span>
          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-slate-400">西</span>
          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-slate-400">东</span>
          <div className="absolute h-7 w-px rounded-full" style={{ backgroundColor: gt.accent }} />
          <div
            className="absolute h-px w-7 rounded-full opacity-50"
            style={{ backgroundColor: gt.accent }}
          />
          <div
            className="absolute left-1/2 top-2 h-0 w-0 -translate-x-1/2 border-x-[5px] border-b-[8px] border-x-transparent"
            style={{ borderBottomColor: gt.accent }}
          />
        </div>
        <span className="mt-1 text-[10px] text-slate-500">南北中轴说 · inference</span>
      </div>

      {/* 美术画廊：整园 AI 工笔大图（方位仅示意，非交互层） */}
      {galleryOpen && scene.gallery && (
        <div
          className="absolute inset-0 z-20 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="大观园美术画廊"
        >
          <div className="relative max-h-[92vh] w-[min(96vw,1100px)] overflow-auto rounded-xl border border-white/15 bg-slate-900/95 p-4 shadow-2xl">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-bold text-slate-100">大观园 · 美术画廊</div>
                <p className="mt-1 text-sm leading-relaxed text-slate-400">
                  整园工笔风格大图，仅作美术欣赏；方位与距离以左侧沙盘 /{' '}
                  <a href="/honglou/map" className="underline decoration-dotted underline-offset-2 text-amber-200/90">
                    2D 地图
                  </a>{' '}
                  为准，勿按此图理解方位。
                </p>
              </div>
              <button
                type="button"
                onClick={() => setGalleryOpen(false)}
                className="shrink-0 text-sm text-slate-400 hover:text-white"
              >
                关闭
              </button>
            </div>
            <img
              src={scene.gallery}
              alt="大观园整园美术大图（方位仅示意）"
              className="mx-auto max-w-full rounded-lg border border-white/10"
            />
          </div>
        </div>
      )}

      {/* NPC 对话 */}
      {dialogue && (
        <div className="absolute bottom-6 left-1/2 z-10 w-[min(92vw,640px)] -translate-x-1/2 rounded-2xl border bg-slate-900/92 p-5 shadow-2xl backdrop-blur-md"
          style={{ borderColor: gt.accentLine }}
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-lg font-bold" style={{ color: hexToNum(dialogue.npc.tint) ? dialogue.npc.tint : gt.accentSoft }}>
              {dialogue.npc.name}
            </span>
            <button
              type="button"
              onClick={() => setDialogue(null)}
              className="text-sm text-slate-400 hover:text-white"
            >
              关闭
            </button>
          </div>
          <p className="mb-3 text-lg leading-relaxed text-slate-100">「{dialogue.line.text}」</p>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">第{dialogue.line.chapter}回</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => rollDialogue(dialogue.npc)}
                className="rounded-lg border border-white/10 px-3 py-1.5 text-sm font-medium text-slate-200 hover:border-white/25 hover:bg-white/5"
              >
                再说一句
              </button>
              {dialogue.npc.link && (
                <a
                  href={dialogue.npc.link}
                  className="rounded-lg px-3 py-1.5 text-sm font-semibold text-slate-900"
                  style={{ backgroundColor: gt.accent }}
                >
                  人物词条 →
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
