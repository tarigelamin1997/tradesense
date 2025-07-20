import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	// Return debug information about the environment
	const debugInfo = {
		timestamp: new Date().toISOString(),
		environment: {
			NODE_ENV: process.env.NODE_ENV,
			VERCEL: process.env.VERCEL,
			VERCEL_ENV: process.env.VERCEL_ENV,
			VERCEL_URL: process.env.VERCEL_URL,
			VITE_API_URL: process.env.VITE_API_URL,
			PUBLIC_API_URL: process.env.PUBLIC_API_URL,
		},
		runtime: {
			node_version: process.version,
			platform: process.platform,
			memory: process.memoryUsage(),
		},
		message: 'Debug endpoint working'
	};

	return json(debugInfo);
};