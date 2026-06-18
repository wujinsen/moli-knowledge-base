#!/usr/bin/env node
/**
 * 只打包 dist/ 内容（压缩包根目录即 index.html），不要打包整个 classical-novels 源码目录。
 */
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const appDir = process.cwd();
const distDir = path.join(appDir, 'dist');
const releaseDir = path.join(appDir, 'release');

function fail(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

if (!fs.existsSync(path.join(distDir, 'index.html'))) {
  fail('dist/index.html 不存在。请先完整执行 npm run build（不要中断）。');
}

for (const name of ['honglou', '_astro', 'pagefind']) {
  if (!fs.existsSync(path.join(distDir, name))) {
    fail(`dist/${name}/ 不存在，构建不完整。`);
  }
}

if (!fs.existsSync(path.join(distDir, 'pagefind', 'pagefind-entry.json'))) {
  fail('dist/pagefind/ 无索引，站内检索会报错。请重新 npm run build。');
}

fs.mkdirSync(releaseDir, { recursive: true });

const stamp = new Date().toISOString().slice(0, 10);
const tarOut = path.join(releaseDir, `classical-novels-dist-${stamp}.tar.gz`);

try {
  execSync(`tar -czf "${tarOut}" -C dist .`, { stdio: 'inherit', cwd: appDir });
} catch {
  fail('tar 打包失败（Windows 10+ / Linux 均自带 tar）');
}

console.log(`\nOK: ${tarOut}`);
console.log('  压缩包根目录 = index.html（不是 dist/index.html 嵌套）');
console.log('  服务器解压:');
console.log('    sudo mkdir -p /opt/chinese-classical-texts/dist');
console.log('    sudo tar -xzf classical-novels-dist-*.tar.gz -C /opt/chinese-classical-texts/dist/');
console.log('    ls /opt/chinese-classical-texts/dist/index.html');
