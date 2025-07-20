// @ts-nocheck
import type { LayoutLoad } from './$types';

export const load = async () => {
	// Authentication initialization moved to +layout.svelte onMount
	// This prevents SSR errors on Vercel
	return {};
};;null as any as LayoutLoad;