#!/usr/bin/env node
/**
 * Dev 模式下 astro-pagefind 从 dist/pagefind/ 提供检索 bundle。
 * npm run clean / dev:clean 会删掉 dist，导致 /search 报 Could not load search bundle。
 * 本脚本在缺失时：有 dist HTML → 仅索引；否则 → astro build（带重试）。
 */
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createIndex } from 'pagefind';

const appDir = process.cwd();
const distDir = path.join(appDir, 'dist');
const entry = path.join(distDir, 'pagefind', 'pagefind-entry.json');
const lockFile = path.join(appDir, '.astro-build.lock');
const BUILD_ATTEMPTS = 3;

// 默认 dev 路径下不触发昂贵的全量 astro build（约 80s）。
// 仅在显式 `--build` / PAGEFIND_ALLOW_BUILD=1 时才允许从零构建生成索引。
const ALLOW_BUILD =
  process.argv.includes('--build') || process.env.PAGEFIND_ALLOW_BUILD === '1';

/** 清除 Astro 构建产物，避免 .prerender 引用已失效的 hash chunk（ERR_MODULE_NOT_FOUND） */
function rmDirSafe(dir) {
  if (!fs.existsSync(dir)) return;
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      fs.rmSync(dir, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 });
      return;
    } catch (err) {
      if (attempt === 4) throw err;
    }
  }
}

function cleanBuildArtifacts() {
  // 只清理与 .prerender chunk 引用失效相关的 dist/、.astro/。
  // 刻意保留 node_modules/.vite（Vite 依赖预打包缓存：echarts/leaflet/pixi/react），
  // 否则下一次 dev 启动会被迫重新 optimize，拖慢冷启动。
  for (const name of ['dist', '.astro']) {
    rmDirSafe(path.join(appDir, name));
  }
  console.log('[pagefind] 已清理 dist/、.astro/（保留 node_modules/.vite 依赖缓存）');
}

function hasBundle() {
  return fs.existsSync(entry);
}

function distLooksComplete() {
  return fs.existsSync(path.join(distDir, 'index.html'));
}

function acquireBuildLock() {
  if (!fs.existsSync(lockFile)) {
    fs.writeFileSync(lockFile, String(process.pid));
    return;
  }
  let owner = fs.readFileSync(lockFile, 'utf8').trim();
  try {
    process.kill(Number(owner), 0);
    console.error(
      `[pagefind] 已有 astro build 在运行 (pid ${owner})。请等待结束，或删除 ${lockFile} 后重试。`,
    );
    process.exit(1);
  } catch {
    fs.unlinkSync(lockFile);
    fs.writeFileSync(lockFile, String(process.pid));
  }
}

function releaseBuildLock() {
  try {
    if (fs.existsSync(lockFile)) fs.unlinkSync(lockFile);
  } catch {
    /* ignore */
  }
}

function runAstroBuildWithRetry() {
  acquireBuildLock();
  try {
    for (let attempt = 1; attempt <= BUILD_ATTEMPTS; attempt += 1) {
      if (attempt > 1) {
        console.log(`[pagefind] build 失败，清理后重试 (${attempt}/${BUILD_ATTEMPTS})…`);
        cleanBuildArtifacts();
      }
      try {
        execSync('npx astro build', { stdio: 'inherit', cwd: appDir, env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' } });
        if (!distLooksComplete()) {
          throw new Error('dist/index.html 未生成');
        }
        return;
      } catch (err) {
        if (attempt === BUILD_ATTEMPTS) throw err;
      }
    }
  } finally {
    releaseBuildLock();
  }
}

async function indexDist() {
  console.log('[pagefind] dist/pagefind 缺失，正在对 dist/ 建索引…');
  const { index, errors } = await createIndex({ loglevel: 'warning' });
  if (!index) {
    errors.forEach((e) => console.error(e));
    process.exit(1);
  }
  const { page_count, errors: addErrors } = await index.addDirectory({ path: distDir });
  if (addErrors.length) {
    addErrors.forEach((e) => console.error(e));
    process.exit(1);
  }
  const { outputPath, errors: writeErrors } = await index.writeFiles({
    outputPath: path.join(distDir, 'pagefind'),
  });
  if (writeErrors.length) {
    writeErrors.forEach((e) => console.error(e));
    process.exit(1);
  }
  console.log(`[pagefind] OK → ${outputPath} (${page_count} pages)`);
}

async function main() {
  if (hasBundle()) return; // 索引已就绪 → 秒过

  if (!distLooksComplete()) {
    if (!ALLOW_BUILD) {
      // dev 默认路径：不做全量 build，立即让 astro dev 启动。
      // /search 在生成索引前不可用，给出明确提示即可。
      console.log('[pagefind] 未发现 dist/，跳过搜索索引构建，dev 直接启动。');
      console.log('[pagefind] 需要站内搜索时执行：npm run dev:search 或 npm run build。');
      return;
    }
    console.log('[pagefind] dist/ 不完整，执行 astro build 生成搜索索引（--build）…');
    cleanBuildArtifacts();
    try {
      runAstroBuildWithRetry();
    } catch {
      console.error(
        '[pagefind] astro build 在多次重试后仍失败。',
        '常见原因：并发的 dev/build 争用 dist/，或 Windows 锁文件。',
        '请关闭其他 dev 实例后执行：npm run clean && npm run dev:search',
      );
      process.exit(1);
    }
    if (!hasBundle()) {
      console.error('[pagefind] build 完成但仍无 pagefind 索引，请检查 astro-pagefind 集成');
      process.exit(1);
    }
    return;
  }

  // 有完整 dist 但缺 pagefind 索引 → 仅建索引（快）
  await indexDist();
}

main().catch((err) => {
  releaseBuildLock();
  console.error(err);
  process.exit(1);
});
