import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Application,
  Assets,
  Container,
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
  water: '/honglou/scene/water.png',
  trees: '/honglou/scene/trees.png',
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

  const [selected, setSelected] = useState<SceneBuilding | null>(null);
  const [dialogue, setDialogue] = useState<{ npc: SceneNpc; line: DialogueLine } | null>(null);
  const [sceneReady, setSceneReady] = useState(false);
  const [sceneError, setSceneError] = useState<string | null>(null);
  const [zoneFilter, setZoneFilter] = useState<string>('all');
  const [scanOpen, setScanOpen] = useState(false);
  const [galleryOpen, setGalleryOpen] = useState(false);

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

      // 水系：中轴溪 + 主湖（环绕「水系」节点质心），用水面纹理填充
      const waterNodes = buildings.filter((b) => b.zone === '水系');
      const axisN = logicalToScene(400, 85, scene.width, scene.height);
      const axisS = logicalToScene(400, 535, scene.width, scene.height);
      let lake = logicalToScene(470, 245, scene.width, scene.height);
      if (waterNodes.length) {
        lake = {
          x: waterNodes.reduce((s, b) => s + center(b).x, 0) / waterNodes.length,
          y: waterNodes.reduce((s, b) => s + center(b).y, 0) / waterNodes.length,
        };
      }
      const waterShape = new Graphics();
      waterShape.moveTo(axisN.x - 24, axisN.y);
      waterShape.bezierCurveTo(axisN.x - 58, lake.y - 90, lake.x + 30, lake.y + 60, axisS.x + 16, axisS.y);
      waterShape.lineTo(axisS.x - 22, axisS.y);
      waterShape.bezierCurveTo(lake.x - 26, lake.y + 70, axisN.x - 86, lake.y - 70, axisN.x - 64, axisN.y);
      waterShape.closePath();
      waterShape.fill({ color: 0xffffff });
      waterShape.ellipse(lake.x, lake.y, 170, 110).fill({ color: 0xffffff });
      const waterFill = new TilingSprite({ texture: tex[SCENE_ASSETS.water], width: gW, height: gH });
      waterFill.position.set(gX, gY);
      waterFill.tileScale.set(0.55);
      waterFill.mask = waterShape;
      world.addChild(waterShape, waterFill);
      // 水岸描边
      const waterEdge = new Graphics();
      waterEdge.ellipse(lake.x, lake.y, 170, 110).stroke({ width: 3, color: 0xe2f3ec, alpha: 0.28 });
      world.addChild(waterEdge);

      // 园墙（双线）
      const wall = new Graphics();
      wall.roundRect(gX, gY, gW, gH, 18).stroke({ width: 7, color: 0x6b5f54 });
      wall.roundRect(gX, gY, gW, gH, 18).stroke({ width: 2, color: 0x9c8e7d, alpha: 0.7 });
      world.addChild(wall);

      // 第17回游线（淡）
      if (scene.paths.length) {
        const tline = new Graphics();
        scene.paths.forEach((p) => {
          const a = buildingById.get(p.from);
          const b = buildingById.get(p.to);
          if (!a || !b) return;
          const ca = center(a);
          const cb = center(b);
          tline.moveTo(ca.x, ca.y).lineTo(cb.x, cb.y);
        });
        tline.stroke({ width: 2, color: 0xe7c873, alpha: 0.22 });
        world.addChild(tline);
      }

      // ============ 林木 + 建筑：按 baseY 统一深度排序 ============
      const labelSize = compactLabels ? 13 : 17;
      const drawables: Array<{ baseY: number; node: Container }> = [];
      const labelLayer = new Container();

      // 林木散点（确定性；避开建筑与水面）
      const rnd = mulberry32(20260616);
      const treeTex = tex[SCENE_ASSETS.trees];
      const treeRatio = treeTex.height / treeTex.width;
      let placed = 0;
      for (let i = 0; i < 900 && placed < 120; i++) {
        const tx = gX + 24 + rnd() * (gW - 48);
        const ty = gY + 24 + rnd() * (gH - 48);
        const nearBuilding = buildings.some(
          (b) => Math.hypot(center(b).x - tx, center(b).y - ty) < 50,
        );
        const inLake = Math.hypot((lake.x - tx) / 1.6, lake.y - ty) < 108;
        if (nearBuilding || inLake) continue;
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
        const isSelected = selected?.id === b.id;
        const node = new Container();
        node.eventMode = 'static';
        node.cursor = 'pointer';
        node.position.set(ground.x, ground.y);

        if (isSelected) {
          const ring = new Graphics();
          ring.ellipse(0, 0, b.w * 0.6, b.h * 0.3).fill({ color: 0xf4d796, alpha: 0.16 });
          ring.ellipse(0, 0, b.w * 0.6, b.h * 0.3).stroke({ width: 2.5, color: 0xf4d796, alpha: 0.85 });
          node.addChild(ring);
        }

        const archTex = tex[SCENE_ASSETS[archetypeFor(b)]];
        let dispW = b.w * 1.2;
        let dispH = b.h;
        if (archTex) {
          const ratio = archTex.height / archTex.width;
          dispH = dispW * ratio;
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

        node.on('pointertap', () => {
          setSelected(b);
          setDialogue(null);
        });
        drawables.push({ baseY: ground.y, node });

        // 名称标签（统一置顶层，避免被南侧建筑遮挡）
        const nameText = new Text({
          text: b.name,
          style: {
            fontFamily: 'Noto Serif SC, serif',
            fontSize: labelSize,
            fill: isSelected ? 0xf4d796 : 0xfdf6e3,
            fontWeight: isSelected ? 700 : 600,
          },
        });
        nameText.anchor.set(0.5, 0);
        const nameBg = new Graphics();
        nameBg
          .roundRect(-nameText.width / 2 - 8, -3, nameText.width + 16, nameText.height + 6, 5)
          .fill({ color: isSelected ? 0x1a120d : 0x16110e, alpha: isSelected ? 0.8 : 0.52 })
          .stroke({ width: 1, color: 0xc5b08f, alpha: isSelected ? 0.65 : 0.3 });
        const nameTag = new Container();
        nameTag.addChild(nameBg, nameText);
        nameTag.position.set(ground.x, ground.y + 8);
        labelLayer.addChild(nameTag);
      }

      drawables.sort((a, b) => a.baseY - b.baseY);
      for (const d of drawables) world.addChild(d.node);
      world.addChild(labelLayer);

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

      // ---- 适配缩放 + 平移 + 滚轮 ----
      const fit = () => {
        const sw = app.screen.width;
        const sh = app.screen.height;
        const s = Math.min(sw / scene.width, sh / scene.height) * 0.94;
        world.scale.set(s);
        world.position.set((sw - scene.width * s) / 2, (sh - scene.height * s) / 2);
        app.stage.hitArea = new Rectangle(0, 0, sw, sh);
      };
      fit();

      app.stage.eventMode = 'static';
      let dragging = false;
      let startP = { x: 0, y: 0 };
      let origin = { x: 0, y: 0 };
      app.stage.on('pointerdown', (e) => {
        dragging = true;
        startP = { x: e.global.x, y: e.global.y };
        origin = { x: world.x, y: world.y };
      });
      const endDrag = () => {
        dragging = false;
      };
      app.stage.on('pointerup', endDrag);
      app.stage.on('pointerupoutside', endDrag);
      app.stage.on('pointermove', (e) => {
        if (!dragging) return;
        world.x = origin.x + (e.global.x - startP.x);
        world.y = origin.y + (e.global.y - startP.y);
      });

      const onWheel = (e: WheelEvent) => {
        e.preventDefault();
        const rect = app.canvas.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        const wx = (px - world.x) / world.scale.x;
        const wy = (py - world.y) / world.scale.y;
        const factor = e.deltaY < 0 ? 1.12 : 0.89;
        const next = Math.max(0.25, Math.min(4, world.scale.x * factor));
        world.scale.set(next);
        world.x = px - wx * next;
        world.y = py - wy * next;
      };
      app.canvas.addEventListener('wheel', onWheel, { passive: false });
      cleanups.push(() => app.canvas.removeEventListener('wheel', onWheel));

      const onResize = () => fit();
      window.addEventListener('resize', onResize);
      window.addEventListener('graph-chrome-sync', onResize);
      cleanups.push(() => {
        window.removeEventListener('resize', onResize);
        window.removeEventListener('graph-chrome-sync', onResize);
      });

      const ro = new ResizeObserver(() => fit());
      ro.observe(host);
      cleanups.push(() => ro.disconnect());

      setSceneReady(true);

      // 暴露 reset
      (app as unknown as { _fit?: () => void })._fit = fit;
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
  }, [scene, visibleBuildings, npcs, buildingById, compactLabels, selected?.id]);

  const resetView = () => {
    const app = appRef.current as (Application & { _fit?: () => void }) | null;
    app?._fit?.();
  };

  return (
    <div
      className="garden-scene graph-explorer relative overflow-hidden"
      style={{ background: gt.backdrop, height: graphHeight, minHeight: graphHeight }}
    >
      <div ref={hostRef} className="absolute inset-0" />

      {!sceneReady && !sceneError && (
        <div className="pointer-events-none absolute inset-0 z-[5] flex items-center justify-center">
          <p className="rounded-lg border border-white/10 bg-slate-900/80 px-4 py-2 text-sm text-slate-300">
            加载大观园实景…
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
        {scene.scale_note && (
          <div className="mt-1.5 text-xs leading-relaxed text-slate-400">{scene.scale_note}</div>
        )}
        <div className="mt-1.5 text-xs text-slate-500">
          点院名标签看方位距离 · 点人物随机说一句 · 滚轮缩放 · 拖拽平移
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
            <a
              href="/honglou/t/scan地图与项目坐标对照"
              className="underline decoration-dotted underline-offset-2 text-slate-400 hover:text-slate-200"
            >
              scan 参考图对照表 →
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
        {scene.scan_reference && (
          <button
            type="button"
            onClick={() => setScanOpen(true)}
            className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/25 hover:text-white"
          >
            scan 参考图
          </button>
        )}
        <button
          type="button"
          onClick={resetView}
          className="rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/25 hover:text-white"
        >
          重置视图
        </button>
      </div>

      {/* 建筑详情 */}
      {selected && (
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
              className="inline-block rounded border border-white/10 px-3 py-1.5 text-sm font-medium text-slate-200 hover:border-white/25 hover:bg-white/5"
            >
              查看建筑词条 →
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

      {/* scan 等距参考图（方位不可采信，仅视觉对照） */}
      {scanOpen && scene.scan_reference && (
        <div
          className="absolute inset-0 z-20 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="scan 参考图"
        >
          <div className="relative max-h-[92vh] w-[min(96vw,920px)] overflow-auto rounded-xl border border-white/15 bg-slate-900/95 p-4 shadow-2xl">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-bold text-slate-100">raw/scan 等距参考图</div>
                <p className="mt-1 text-sm leading-relaxed text-slate-400">
                  AI 生成示意图，23 处编号。建筑落位以本页 Pixi 场景与{' '}
                  <a href="/honglou/map" className="underline decoration-dotted underline-offset-2 text-amber-200/90">
                    2D 地图
                  </a>{' '}
                  为准，勿按此图方位理解。
                </p>
              </div>
              <button
                type="button"
                onClick={() => setScanOpen(false)}
                className="shrink-0 text-sm text-slate-400 hover:text-white"
              >
                关闭
              </button>
            </div>
            <img
              src={scene.scan_reference}
              alt="大观园 scan 等距参考图（方位仅供参考）"
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
