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

interface SceneBuilding {
  id: string;
  name: string;
  plaque?: string;
  zone: string;
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
  px_per_step: number;
  scale_note?: string;
  buildings: SceneBuilding[];
  npcs: SceneNpc[];
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

export default function GardenScene({ scene, pools, bookSlug }: Props) {
  const gt = useMemo(() => graphTheme(bookSlug), [bookSlug]);
  const hostRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);

  const [selected, setSelected] = useState<SceneBuilding | null>(null);
  const [dialogue, setDialogue] = useState<{ npc: SceneNpc; line: DialogueLine } | null>(null);

  const buildingById = useMemo(
    () => new Map(scene.buildings.map((b) => [b.id, b])),
    [scene.buildings],
  );

  const distancesFrom = useMemo(() => {
    if (!selected) return [];
    const c0 = center(selected);
    return scene.buildings
      .filter((b) => b.id !== selected.id)
      .map((b) => {
        const c = center(b);
        const px = Math.hypot(c.x - c0.x, c.y - c0.y);
        return { id: b.id, name: b.name, steps: Math.round(px / scene.px_per_step) };
      })
      .sort((a, b) => a.steps - b.steps);
  }, [selected, scene.buildings, scene.px_per_step]);

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

    (async () => {
      await app.init({
        antialias: true,
        backgroundAlpha: 0,
        resizeTo: host,
        resolution: Math.min(window.devicePixelRatio || 1, 2),
        autoDensity: true,
      });
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
      // 沁芳溪：横贯的水带
      bg.moveTo(40, 250);
      bg.bezierCurveTo(360, 200, 760, 320, scene.width - 40, 270);
      bg.lineTo(scene.width - 40, 360);
      bg.bezierCurveTo(760, 410, 360, 300, 40, 350);
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

        const steps = Math.round(Math.hypot(cb.x - ca.x, cb.y - ca.y) / scene.px_per_step);
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

      for (const b of scene.buildings) {
        const node = new Container();
        node.position.set(b.x, b.y);
        node.eventMode = 'static';
        node.cursor = 'pointer';

        const placeholder = drawPlaceholderBuilding(b);
        node.addChild(placeholder);

        // 匾额 + 名称
        const nameTag = new Container();
        const nameText = new Text({
          text: b.plaque ? `${b.name}（${b.plaque}）` : b.name,
          style: {
            fontFamily: 'Noto Serif SC, serif',
            fontSize: 18,
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
              sp.width = b.w;
              sp.height = b.h;
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
      for (const n of scene.npcs) {
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
              sp.anchor.set(0.5, 1);
              sp.width = 70;
              sp.height = 110;
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
      cleanups.push(() => window.removeEventListener('resize', onResize));

      // 暴露 reset
      (app as unknown as { _fit?: () => void })._fit = fit;
    })();

    return () => {
      disposed = true;
      cleanups.forEach((fn) => fn());
      if (appRef.current) {
        appRef.current.destroy(true, { children: true });
        appRef.current = null;
      }
    };
  }, [scene, buildingById]);

  const resetView = () => {
    const app = appRef.current as (Application & { _fit?: () => void }) | null;
    app?._fit?.();
  };

  return (
    <div
      className="garden-scene relative min-h-[calc(100vh-3rem)] overflow-hidden"
      style={{ background: gt.backdrop }}
    >
      <div ref={hostRef} className="absolute inset-0" />

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
      </div>

      <button
        type="button"
        onClick={resetView}
        className="absolute right-3 top-3 z-10 rounded-lg border border-white/10 bg-slate-900/80 px-3.5 py-2 text-sm font-medium text-slate-200 backdrop-blur-sm hover:border-white/25 hover:text-white"
      >
        重置视图
      </button>

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
          <div className="mb-1.5 text-sm font-semibold text-slate-400">到其他建筑（示意）</div>
          <ul className="mb-3 flex flex-col gap-1">
            {distancesFrom.map((d) => (
              <li key={d.id} className="flex justify-between text-sm text-slate-200">
                <span>{d.name}</span>
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
