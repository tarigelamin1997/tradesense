import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	return json({
		status: 'ok',
		timestamp: new Date().toISOString(),
		message: 'Frontend health check endpoint',
		environment: {
			NODE_ENV: process.env.NODE_ENV || 'unknown',
			HAS_VITE_API_URL: !!process.env.VITE_API_URL
		}
	});
};