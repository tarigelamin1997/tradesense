// @ts-nocheck
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load = async ({ locals }: Parameters<PageServerLoad>[0]) => {
	// Protect this route - redirect to login if not authenticated
	if (!locals.isAuthenticated) {
		throw redirect(303, '/login');
	}
	
	// Pass user data to the page
	return {
		user: locals.user
	};
};