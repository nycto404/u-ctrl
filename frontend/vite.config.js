import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
    plugins: [vue()],
    server: {
        host: true,
        port: 5173,
        strictPort: true
    },
    build: {
        outDir: '../app/static/dist',
        emptyOutDir: true,
        assetsDir: 'assets',
        sourcemap: false,
        cssCodeSplit: false,
        rollupOptions: {
            output: {
                entryFileNames: 'assets/app.js',
                chunkFileNames: 'assets/[name].js',
                assetFileNames: (assetInfo) => {
                    if (assetInfo.name && assetInfo.name.endsWith('.css')) {
                        return 'assets/app.css';
                    }
                    return 'assets/[name][extname]';
                }
            }
        }
    }
});
