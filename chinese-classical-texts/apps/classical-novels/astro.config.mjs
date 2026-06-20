import fs from 'node:fs';
import path from 'node:path';
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import pagefind from 'astro-pagefind';
import tailwindcss from '@tailwindcss/vite';

/** 行数超过该阈值的 Markdown 表格默认折叠为可展开 <details> */
const FOLD_TABLE_ROW_THRESHOLD = 12;

/* ===== [[名物]] / [[主题]] wiki 链接解析（构建期建索引） ===== */
const CONTENT_DIR = path.resolve('./src/content');
const ITEM_COLLECTIONS = ['dishes', 'medicines', 'costumes', 'customs', 'artifacts'];

/** 书名 → slug（取自 books/*.md frontmatter） */
function loadBookSlugMap() {
  const map = {};
  const dir = path.join(CONTENT_DIR, 'books');
  if (!fs.existsSync(dir)) return map;
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith('.md')) continue;
    const txt = fs.readFileSync(path.join(dir, f), 'utf8');
    const book = /(^|\n)book:\s*(\S+)/.exec(txt)?.[2];
    const slug = /(^|\n)slug:\s*(\S+)/.exec(txt)?.[2];
    if (book && slug) map[book] = slug;
  }
  return map;
}

/** 书名 → { items:Set<文件名>, topics:Set<文件名> } */
function buildWikiIndex() {
  const idx = {};
  const ensure = (b) => (idx[b] ??= { items: new Set(), topics: new Set() });
  const scan = (collDir, into) => {
    if (!fs.existsSync(collDir)) return;
    for (const book of fs.readdirSync(collDir)) {
      const bdir = path.join(collDir, book);
      if (!fs.statSync(bdir).isDirectory()) continue;
      for (const f of fs.readdirSync(bdir)) {
        if (f.endsWith('.md')) ensure(book)[into].add(f.replace(/\.md$/, ''));
      }
    }
  };
  for (const coll of ITEM_COLLECTIONS) scan(path.join(CONTENT_DIR, coll), 'items');
  scan(path.join(CONTENT_DIR, 'topics'), 'topics');
  return idx;
}

const BOOK_SLUG = loadBookSlugMap();
const WIKI_INDEX = buildWikiIndex();

function bookFromVFilePath(p) {
  if (!p) return null;
  const norm = p.replace(/\\/g, '/');
  const m = norm.match(/\/content\/[^/]+\/([^/]+)\//);
  return m ? m[1] : null;
}

/** 解析 [[目标]] → {href} 或 null（未命中） */
function resolveWikiTarget(book, target) {
  const slug = BOOK_SLUG[book];
  const e = WIKI_INDEX[book];
  if (!slug || !e) return null;
  if (e.topics.has(target)) return { href: `/${slug}/topics/${target}` };
  if (e.items.has(target)) return { href: `/${slug}/i/${target}` };
  return null;
}

const WIKILINK_RE = /\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]/g;

/** 把正文中的 [[目标]] / [[目标|别名]] 转成链接；未命中渲染为弱化 span */
function rehypeWikiLinks() {
  return (tree, file) => {
    const book = bookFromVFilePath(file?.path || file?.history?.[0]);
    if (!book) return;
    const SKIP = new Set(['a', 'code', 'pre']);
    const walk = (node) => {
      const children = node.children;
      if (!children) return;
      for (let i = 0; i < children.length; i += 1) {
        const child = children[i];
        if (child.type === 'element') {
          if (SKIP.has(child.tagName)) continue;
          walk(child);
          continue;
        }
        if (child.type !== 'text' || !child.value.includes('[[')) continue;
        const out = [];
        let last = 0;
        let m;
        WIKILINK_RE.lastIndex = 0;
        while ((m = WIKILINK_RE.exec(child.value))) {
          const [full, target, label] = m;
          if (m.index > last) out.push({ type: 'text', value: child.value.slice(last, m.index) });
          const text = (label || target).trim();
          const hit = resolveWikiTarget(book, target.trim());
          if (hit) {
            out.push({
              type: 'element',
              tagName: 'a',
              properties: { href: hit.href, className: ['wikilink'] },
              children: [{ type: 'text', value: text }],
            });
          } else {
            out.push({
              type: 'element',
              tagName: 'span',
              properties: { className: ['wikilink', 'wikilink--missing'], title: '未建页' },
              children: [{ type: 'text', value: text }],
            });
          }
          last = m.index + full.length;
        }
        if (!out.length) continue;
        if (last < child.value.length) out.push({ type: 'text', value: child.value.slice(last) });
        children.splice(i, 1, ...out);
        i += out.length - 1;
      }
    };
    walk(tree);
  };
}

function firstElementChild(node, tagName) {
  return (node.children || []).find((c) => c.type === 'element' && c.tagName === tagName);
}

function countTableRows(table) {
  const tbody = firstElementChild(table, 'tbody');
  const scope = tbody ?? table;
  let rows = 0;
  const walk = (n) => {
    for (const c of n.children || []) {
      if (c.type !== 'element') continue;
      if (c.tagName === 'tr') rows += 1;
      else walk(c);
    }
  };
  walk(scope);
  if (!tbody) rows = Math.max(0, rows - 1); // 去掉表头行
  return rows;
}

/** 把长表格包进 <details class="md-fold-table">，默认折叠 */
function rehypeFoldLongTables() {
  return (tree) => {
    const walk = (node) => {
      const children = node.children;
      if (!children) return;
      for (let i = 0; i < children.length; i += 1) {
        const child = children[i];
        if (child.type === 'element' && child.tagName === 'table') {
          const rows = countTableRows(child);
          if (rows > FOLD_TABLE_ROW_THRESHOLD) {
            children[i] = {
              type: 'element',
              tagName: 'details',
              properties: { className: ['md-fold-table'] },
              children: [
                {
                  type: 'element',
                  tagName: 'summary',
                  properties: { className: ['md-fold-table__summary'] },
                  children: [{ type: 'text', value: `表格 · ${rows} 行` }],
                },
                child,
              ],
            };
            continue;
          }
        }
        walk(child);
      }
    };
    walk(tree);
  };
}

export default defineConfig({
  site: 'https://chinese-classical-texts.wu-jinsen.com',
  integrations: [react(), pagefind()],
  markdown: {
    // 关闭 Shiki 深色高亮（代码块多为 ASCII 示意/纯文本），改用纸色主题 CSS 渲染
    syntaxHighlight: false,
    rehypePlugins: [rehypeWikiLinks, rehypeFoldLongTables],
  },
  // 严格 CSP 环境下 dev toolbar / HMR 会触发 eval 警告；生产构建不依赖 eval
  devToolbar: { enabled: false },
  // Windows 上高并发 prerender 偶发 .prerender/chunks 引用缺失（ERR_MODULE_NOT_FOUND）
  build: { concurrency: 1 },
  vite: {
    plugins: [tailwindcss()],
    optimizeDeps: {
      include: ['leaflet', 'react', 'react-dom', 'echarts/core'],
    },
    ssr: {
      noExternal: ['leaflet'],
    },
    build: {
      rollupOptions: {
        output: {
          // 把 echarts/zrender 收进单一共享 chunk，避免被各 client:only island 重复打包
          manualChunks(id) {
            if (id.includes('node_modules/echarts') || id.includes('node_modules/zrender')) {
              return 'echarts';
            }
          },
        },
      },
    },
  },
  server: {
    proxy: {
      '/api/studio': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
      },
    },
  },
});
