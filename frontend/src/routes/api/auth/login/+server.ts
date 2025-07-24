import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { AuthService } from '$lib/server/auth';
import { api } from '$lib/api/client';

export const POST: RequestHandler = async ({ request, cookies }) => {
	try {
		const { email, password } = await request.json();
		
		// Call backend API to authenticate
		const response = await api.post('/api/v1/auth/login', {
			email,
			password
		});
		
		const { user, token, refresh_token } = response.data;
		
		// Set secure httpOnly cookies
		AuthService.setAuthCookies(cookies, token, refresh_token, user);
		
		// Return user data (but not the token - it's in httpOnly cookie)
		return json({
			success: true,
			user
		});
	} catch (error: any) {
		console.error('Login error:', error);
		
		const message = error.response?.data?.detail || 'Login failed';
		const status = error.response?.status || 500;
		
		return json(
			{
				success: false,
				error: message
			},
			{ status }
		);
	}
};