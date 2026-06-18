import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import pagefind from 'astro-pagefind';

export default defineConfig({
  site: 'https://chinese-classical-texts.wu-jinsen.com',
  integrations: [react(), pagefind()],
  // 严格 CSP 环境下 dev toolbar / HMR 会触发 eval 警告；生产构建不依赖 eval
  devToolbar: { enabled: false },
  // Windows 上高并发 prerender 偶发 .prerender/chunks 引用缺失（ERR_MODULE_NOT_FOUND）
  build: { concurrency: 1 },
  vite: {
    optimizeDeps: {
      include: ['leaflet', 'react', 'react-dom', 'echarts'],
    },
    ssr: {
      noExternal: ['leaflet'],
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
