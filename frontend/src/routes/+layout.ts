import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async () => {
	// Authentication initialization moved to +layout.svelte onMount
	// This prevents SSR errors on Vercel
	return {};
};