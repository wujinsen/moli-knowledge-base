import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import pagefind from 'astro-pagefind';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://chinese-classical-texts.wu-jinsen.com',
  integrations: [react(), pagefind()],
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
