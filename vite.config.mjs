import { defineConfig } from 'vite';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    outDir: resolve(__dirname, 'src/wagtail_feathers/static/js'),
    emptyOutDir: false,
    
    rollupOptions: {
      input: {
        admin: resolve(__dirname, 'frontend/src/javascript/feathers_admin.js'),
      },
      output: {
        entryFileNames: '[name].js',
        format: 'iife',
        manualChunks: undefined,
      },
    },

    cssCodeSplit: false,
    
    minify: false,
  }
});