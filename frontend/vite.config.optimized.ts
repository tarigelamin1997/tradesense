import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';
import compression from 'vite-plugin-compression';

export default defineConfig({
	plugins: [
		sveltekit(),
		// Gzip compression
		compression({
			algorithm: 'gzip',
			ext: '.gz',
			threshold: 1024, // Only compress files > 1KB
		}),
		// Brotli compression
		compression({
			algorithm: 'brotliCompress',
			ext: '.br',
			threshold: 1024,
		}),
		// Bundle size visualization (only in analyze mode)
		process.env.ANALYZE && visualizer({
			filename: './dist/stats.html',
			open: true,
			gzipSize: true,
			brotliSize: true,
		})
	].filter(Boolean),
	
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
			}
		},
		hmr: {
			overlay: false
		}
	},
	
	build: {
		// Production optimizations
		minify: 'terser',
		terserOptions: {
			compress: {
				drop_console: true,
				drop_debugger: true,
				pure_funcs: ['console.log', 'console.info'],
			},
		},
		
		// Code splitting
		rollupOptions: {
			output: {
				manualChunks: {
					// Vendor chunks
					'vendor-svelte': ['svelte', '@sveltejs/kit'],
					'vendor-utils': ['axios', 'date-fns'],
					'vendor-charts': ['chart.js', 'chartjs-adapter-date-fns'],
				},
				// Better chunking strategy
				chunkFileNames: (chunkInfo) => {
					const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk';
					return `assets/js/${facadeModuleId}-[hash].js`;
				},
				assetFileNames: (assetInfo) => {
					const extType = assetInfo.name.split('.').pop();
					if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
						return `assets/images/[name]-[hash][extname]`;
					}
					if (/woff|woff2|eot|ttf|otf/i.test(extType)) {
						return `assets/fonts/[name]-[hash][extname]`;
					}
					return `assets/[ext]/[name]-[hash][extname]`;
				},
			},
		},
		
		// Chunk size warnings
		chunkSizeWarningLimit: 600, // 600KB
		
		// Source maps for production debugging
		sourcemap: true,
		
		// Asset inlining threshold
		assetsInlineLimit: 4096, // 4KB
		
		// CSS code splitting
		cssCodeSplit: true,
		
		// Target modern browsers
		target: 'es2020',
		
		// Report compressed size
		reportCompressedSize: true,
	},
	
	optimizeDeps: {
		include: [
			'axios',
			'svelte',
			'@sveltejs/kit',
			'chart.js',
			'date-fns'
		],
		exclude: ['@sveltejs/kit/node'],
	},
	
	// CSS optimization
	css: {
		devSourcemap: true,
		preprocessorOptions: {
			scss: {
				additionalData: `@import '$lib/styles/variables.scss';`
			}
		}
	},
	
	// Performance hints
	resolve: {
		alias: {
			'$lib': '/src/lib',
			'$components': '/src/lib/components',
			'$stores': '/src/lib/stores',
			'$utils': '/src/lib/utils',
		}
	},
	
	// Preview server configuration
	preview: {
		port: 4173,
		strictPort: true,
		host: true,
	}
});