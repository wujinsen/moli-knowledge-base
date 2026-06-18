import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import pagefind from 'astro-pagefind';

export default defineConfig({
  site: 'https://chinese-classical-texts.wu-jinsen.com',
  integrations: [react(), pagefind()],
  server: {
    proxy: {
      '/api/studio': {
        target: 'http://127.0.0.1:8787',
        changeOrigin: true,
      },
    },
  },
});
