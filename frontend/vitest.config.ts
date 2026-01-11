import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    include: ['src/**/__tests__/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        'dist/**',
        '**/__tests__/**',
        'src/test/**',
        'src/vite-env.d.ts',
        '**/*.d.ts',
        'src/main.tsx',
        'src/App.tsx',
        'src/router/**',
        'src/pages/**',
        'src/components/layout/**',
        'src/components/ui/**',
        'src/components/products/**',
        'src/components/jobs/**',
        'src/components/settings/**',
      ],
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});