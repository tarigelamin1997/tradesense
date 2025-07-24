import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
	plugins: [sveltekit()],
	resolve: {
		alias: {
			$lib: resolve('./src/lib')
		}
	},
	server: {
		port: 3001,
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				configure: (proxy, options) => {
					proxy.on('error', (err, req, res) => {
						console.log('API proxy error:', err);
					});
				}
			},
			'/auth': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				configure: (proxy, options) => {
					proxy.on('error', (err, req, res) => {
						console.log('Auth proxy error:', err);
					});
				}
			}
		},
		hmr: {
			overlay: false
		}
	},
	optimizeDeps: {
		exclude: ['axios'] // Remove axios from optimization since we're not using it
	}
});