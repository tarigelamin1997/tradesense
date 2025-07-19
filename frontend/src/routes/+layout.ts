import type { LayoutLoad } from './$types';
import { auth } from '$lib/api/auth.js';
import { browser } from '$app/environment';

export const load: LayoutLoad = async () => {
	// Check authentication status on initial load
	if (browser) {
		await auth.checkAuth();
	}
	
	return {};
};