import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
	// Pass user data from cookies to the client
	return {
		user: locals.user
	};
};