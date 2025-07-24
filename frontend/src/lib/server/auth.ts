import type { Cookies } from '@sveltejs/kit';
import { dev } from '$app/environment';

const AUTH_COOKIE_NAME = 'tradesense_auth_token';
const USER_COOKIE_NAME = 'tradesense_user';
const REFRESH_COOKIE_NAME = 'tradesense_refresh_token';

// Cookie options for security
const COOKIE_OPTIONS = {
	httpOnly: true,
	secure: !dev, // Use secure cookies in production
	sameSite: 'lax' as const,
	path: '/',
	maxAge: 60 * 60 * 24 * 7 // 7 days
};

const USER_COOKIE_OPTIONS = {
	httpOnly: false, // User data can be read by client
	secure: !dev,
	sameSite: 'lax' as const,
	path: '/',
	maxAge: 60 * 60 * 24 * 7 // 7 days
};

export interface AuthUser {
	id: string;
	email: string;
	name: string;
	subscription_tier: 'free' | 'starter' | 'professional' | 'enterprise';
	is_admin?: boolean;
	mfa_enabled?: boolean;
}

export class AuthService {
	/**
	 * Set authentication cookies
	 */
	static setAuthCookies(cookies: Cookies, token: string, refreshToken: string, user: AuthUser) {
		// Set httpOnly cookie for token (prevents XSS attacks)
		cookies.set(AUTH_COOKIE_NAME, token, COOKIE_OPTIONS);
		
		// Set refresh token
		cookies.set(REFRESH_COOKIE_NAME, refreshToken, {
			...COOKIE_OPTIONS,
			maxAge: 60 * 60 * 24 * 30 // 30 days for refresh token
		});
		
		// Set user data (non-httpOnly so client can read it)
		cookies.set(USER_COOKIE_NAME, JSON.stringify(user), USER_COOKIE_OPTIONS);
	}

	/**
	 * Get authentication token from cookies
	 */
	static getAuthToken(cookies: Cookies): string | null {
		return cookies.get(AUTH_COOKIE_NAME) || null;
	}

	/**
	 * Get refresh token from cookies
	 */
	static getRefreshToken(cookies: Cookies): string | null {
		return cookies.get(REFRESH_COOKIE_NAME) || null;
	}

	/**
	 * Get user data from cookies
	 */
	static getUser(cookies: Cookies): AuthUser | null {
		const userCookie = cookies.get(USER_COOKIE_NAME);
		if (!userCookie) return null;
		
		try {
			return JSON.parse(userCookie) as AuthUser;
		} catch {
			return null;
		}
	}

	/**
	 * Clear all authentication cookies
	 */
	static clearAuthCookies(cookies: Cookies) {
		cookies.delete(AUTH_COOKIE_NAME, { path: '/' });
		cookies.delete(REFRESH_COOKIE_NAME, { path: '/' });
		cookies.delete(USER_COOKIE_NAME, { path: '/' });
	}

	/**
	 * Validate token format (basic validation)
	 */
	static isValidTokenFormat(token: string): boolean {
		// JWT format: header.payload.signature
		const parts = token.split('.');
		return parts.length === 3 && parts.every(part => part.length > 0);
	}

	/**
	 * Extract token expiry from JWT (without verification)
	 */
	static getTokenExpiry(token: string): Date | null {
		try {
			const parts = token.split('.');
			if (parts.length !== 3) return null;
			
			const payload = JSON.parse(atob(parts[1]));
			if (!payload.exp) return null;
			
			return new Date(payload.exp * 1000);
		} catch {
			return null;
		}
	}

	/**
	 * Check if token is expired
	 */
	static isTokenExpired(token: string): boolean {
		const expiry = this.getTokenExpiry(token);
		if (!expiry) return true;
		
		return expiry < new Date();
	}
}