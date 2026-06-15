import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Application,
  Assets,
  Container,
  Graphics,
  Rectangle,
  Sprite,
  Text,
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
  background?: string;
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

function center(b: SceneBuilding) {
  return { x: b.x + b.w / 2, y: b.y + b.h / 2 };
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

      const world = new Container();
      app.stage.addChild(world);

      // ---- 背景 ----
      const bg = new Graphics();
      bg.rect(0, 0, scene.width, scene.height).fill({ color: 0x141d22 });
      // 园地暖色块
      bg.roundRect(20, 20, scene.width - 40, scene.height - 40, 18).fill({ color: 0x20302a });
      // 沁芳溪：沿逻辑中轴（北→南），与 /honglou/map 水系一致
      const axis = logicalToScene(400, 300, scene.width, scene.height);
      bg.moveTo(axis.x - 55, 40);
      bg.bezierCurveTo(axis.x - 80, 180, axis.x + 70, 320, axis.x + 45, scene.height - 40);
      bg.lineTo(axis.x - 25, scene.height - 40);
      bg.bezierCurveTo(axis.x - 50, 320, axis.x + 60, 180, axis.x + 35, 40);
      bg.closePath();
      bg.fill({ color: 0x2c5a73, alpha: 0.55 });
      world.addChild(bg);

      // 背景贴图（若存在则覆盖占位）
      if (scene.background) {
        Assets.load(scene.background)
          .then((tex: Texture) => {
            if (disposed) return;
            const sp = new Sprite(tex);
            sp.width = scene.width;
            sp.height = scene.height;
            sp.alpha = 0.72; // 水彩背景仅氛围；方位以逻辑坐标/罗盘为准
            world.addChildAt(sp, 1);
          })
          .catch(() => {
            /* 占位背景保留 */
          });
      }

      // ---- 距离连线 ----
      const lines = new Graphics();
      world.addChild(lines);
      for (const p of scene.paths) {
        const a = buildingById.get(p.from);
        const b = buildingById.get(p.to);
        if (!a || !b) continue;
        const ca = center(a);
        const cb = center(b);
        lines.moveTo(ca.x, ca.y).lineTo(cb.x, cb.y);
        lines.stroke({ width: 3, color: 0xe0b059, alpha: 0.35 });

        const steps = logicalSteps(a.logical, b.logical, scene.px_per_step);
        const mid = { x: (ca.x + cb.x) / 2, y: (ca.y + cb.y) / 2 };
        const tag = new Container();
        const label = new Text({
          text: `约 ${steps} 步`,
          style: {
            fontFamily: 'Noto Serif SC, serif',
            fontSize: 16,
            fill: 0xf4d796,
            fontWeight: '600',
          },
        });
        label.anchor.set(0.5);
        const pad = new Graphics();
        pad
          .roundRect(-label.width / 2 - 8, -label.height / 2 - 4, label.width + 16, label.height + 8, 6)
          .fill({ color: 0x0a0608, alpha: 0.78 });
        tag.addChild(pad, label);
        tag.position.set(mid.x, mid.y);
        world.addChild(tag);
      }

      // ---- 建筑 ----
      const drawPlaceholderBuilding = (b: SceneBuilding) => {
        const g = new Graphics();
        const fill = ZONE_FILL[b.zone] ?? 0x8a6f4a;
        // 台基
        g.roundRect(0, b.h * 0.55, b.w, b.h * 0.45, 4).fill({ color: 0xcdbf9e, alpha: 0.95 });
        // 墙身
        g.roundRect(b.w * 0.08, b.h * 0.32, b.w * 0.84, b.h * 0.3, 3).fill({ color: 0xeae3d2 });
        // 立柱
        g.rect(b.w * 0.12, b.h * 0.32, b.w * 0.04, b.h * 0.3).fill({ color: 0x7a3b2e });
        g.rect(b.w * 0.84, b.h * 0.32, b.w * 0.04, b.h * 0.3).fill({ color: 0x7a3b2e });
        // 歇山屋顶 + 飞檐
        g.moveTo(-b.w * 0.1, b.h * 0.34);
        g.lineTo(b.w * 1.1, b.h * 0.34);
        g.lineTo(b.w * 0.78, 0);
        g.lineTo(b.w * 0.22, 0);
        g.closePath();
        g.fill({ color: fill });
        // 屋脊
        g.roundRect(b.w * 0.22, -6, b.w * 0.56, 8, 4).fill({ color: 0x2c2420 });
        return g;
      };

      for (const b of visibleBuildings) {
        const node = new Container();
        node.position.set(b.x, b.y);
        node.eventMode = 'static';
        node.cursor = 'pointer';

        const placeholder = drawPlaceholderBuilding(b);
        node.addChild(placeholder);

        // 名称（全园模式仅显示院名，匾在侧栏）
        const nameTag = new Container();
        const nameText = new Text({
          text: b.name,
          style: {
            fontFamily: 'Noto Serif SC, serif',
            fontSize: compactLabels ? 13 : 18,
            fill: 0xfdf6e3,
            fontWeight: '700',
          },
        });
        nameText.anchor.set(0.5, 0);
        const nameBg = new Graphics();
        nameBg
          .roundRect(-nameText.width / 2 - 10, -4, nameText.width + 20, nameText.height + 8, 6)
          .fill({ color: 0x0a0608, alpha: 0.7 });
        nameTag.addChild(nameBg, nameText);
        nameTag.position.set(b.w / 2, b.h + 6);
        node.addChild(nameTag);

        if (b.sprite) {
          Assets.load(b.sprite)
            .then((tex: Texture) => {
              if (disposed) return;
              const sp = new Sprite(tex);
              const ratio = tex.height / tex.width;
              sp.width = b.w;
              sp.height = b.w * ratio;
              sp.x = 0;
              sp.y = b.h - sp.height;
              node.removeChild(placeholder);
              node.addChildAt(sp, 0);
            })
            .catch(() => {
              /* 占位建筑保留 */
            });
        }

        node.on('pointertap', () => {
          setSelected(b);
          setDialogue(null);
        });
        world.addChild(node);
      }

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
          点建筑看方位距离 · 点人物（黛玉 / 宝玉）随机说一句 · 滚轮缩放 · 拖拽平移
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
