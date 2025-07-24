import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { AuthService } from '$lib/server/auth';

export const POST: RequestHandler = async ({ cookies }) => {
	// Clear all auth cookies
	AuthService.clearAuthCookies(cookies);
	
	return json({
		success: true,
		message: 'Logged out successfully'
	});
};