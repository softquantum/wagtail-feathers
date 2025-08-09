import { defineConfig } from 'vite';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig((configEnv) => {

  const isDev = configEnv.mode === 'development';
  const config = {
    build: {
      watch: configEnv.command === 'build' && process.argv.includes('--watch')
        ? {exclude: ['node_modules/**', 'src/wagtail_feathers/static/**']}
        : null,

      cssCodeSplit: false,
      minify: false,
      outDir: resolve(__dirname, 'src/wagtail_feathers/static'),
      emptyOutDir: false,

      rollupOptions: {
        input: {
          wagtail_feathers_admin: resolve(__dirname, 'frontend/src/javascript/admin.js'),
        },
        output: {
          entryFileNames: 'js/[name].js',
          format: 'es',
          manualChunks: undefined,
          assetFileNames: (assetInfo) => {
            if (assetInfo.name?.endsWith('.css')) {
              return 'css/wagtail_feathers_admin.css';
            }
            return 'assets/[name].[ext]';
          },

        },
      },
    }
  }
  return config;
});