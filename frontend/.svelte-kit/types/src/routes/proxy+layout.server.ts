// @ts-nocheck
import type { LayoutServerLoad } from './$types';

export const load = async ({ locals }: Parameters<LayoutServerLoad>[0]) => {
	// Pass user data from cookies to the client
	return {
		user: locals.user
	};
};