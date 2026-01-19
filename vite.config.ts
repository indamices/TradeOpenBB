import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      build: {
        outDir: 'dist',
        sourcemap: false,
        minify: 'esbuild',  // Use esbuild instead of terser (faster, no extra dependency)
        rollupOptions: {
          output: {
            /**
             * 优化代码分割策略
             * 减少初始 bundle 大小，提升加载速度
             */
            manualChunks: (id) => {
              // Vendor 分离（第三方库）
              if (id.includes('node_modules')) {
                // React 核心
                if (id.includes('react') || id.includes('react-dom')) {
                  return 'react-vendor';
                }
                // 图表库（recharts 单独一个 chunk，因为它很大）
                if (id.includes('recharts')) {
                  return 'chart-vendor';
                }
                // UI 库（lucide-react 图标等）
                if (id.includes('lucide-react')) {
                  return 'ui-vendor';
                }
                // 其他第三方库
                return 'vendor';
              }

              // 功能模块分割（按业务功能）
              if (id.includes('/components/Backtest')) {
                return 'backtest-feature';
              }
              if (id.includes('/components/AI') || id.includes('/components/Chat')) {
                return 'ai-feature';
              }
              if (id.includes('/components/Strategy')) {
                return 'strategy-feature';
              }
              if (id.includes('/components/Portfolio')) {
                return 'portfolio-feature';
              }
              if (id.includes('/components/Historical')) {
                return 'data-feature';
              }
            },
          },
        },
        // 优化 chunk 大小警告阈值
        chunkSizeWarningLimit: 600,
      }
    };
});
