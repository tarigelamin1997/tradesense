import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { AuthService } from '$lib/server/auth';
import { api } from '$lib/api/client';

export const POST: RequestHandler = async ({ cookies }) => {
	try {
		const refreshToken = AuthService.getRefreshToken(cookies);
		
		if (!refreshToken) {
			return json(
				{
					success: false,
					error: 'No refresh token found'
				},
				{ status: 401 }
			);
		}
		
		// Call backend API to refresh token
		const response = await api.post('/api/v1/auth/refresh', {
			refresh_token: refreshToken
		});
		
		const { user, token, refresh_token: newRefreshToken } = response.data;
		
		// Update cookies with new tokens
		AuthService.setAuthCookies(cookies, token, newRefreshToken, user);
		
		return json({
			success: true,
			user
		});
	} catch (error: any) {
		console.error('Token refresh error:', error);
		
		// Clear cookies on refresh failure
		AuthService.clearAuthCookies(cookies);
		
		return json(
			{
				success: false,
				error: 'Token refresh failed'
			},
			{ status: 401 }
		);
	}
};