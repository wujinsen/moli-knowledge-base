#!/usr/bin/env node
/**
 * Dev 模式下 astro-pagefind 从 dist/pagefind/ 提供检索 bundle。
 * npm run clean / dev:clean 会删掉 dist，导致 /search 报 Could not load search bundle。
 * 本脚本在缺失时：有 dist HTML → 仅索引；否则 → astro build。
 */
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createIndex } from 'pagefind';

const appDir = process.cwd();
const distDir = path.join(appDir, 'dist');
const entry = path.join(distDir, 'pagefind', 'pagefind-entry.json');

function hasBundle() {
  return fs.existsSync(entry);
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
  if (hasBundle()) return;

  if (!fs.existsSync(path.join(distDir, 'index.html'))) {
    console.log('[pagefind] dist/ 不存在，先执行 astro build（首次 dev 或刚 clean 后）…');
    execSync('npx astro build', { stdio: 'inherit', cwd: appDir });
    if (!hasBundle()) {
      console.error('[pagefind] build 完成但仍无 pagefind 索引，请检查 astro-pagefind 集成');
      process.exit(1);
    }
    return;
  }

  await indexDist();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
