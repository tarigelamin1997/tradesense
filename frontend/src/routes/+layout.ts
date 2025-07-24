import type { LayoutLoad } from './$types';
import { initI18n } from '$lib/i18n';
import { waitLocale } from 'svelte-i18n';

export const load: LayoutLoad = async () => {
	// Initialize i18n
	await initI18n();
	await waitLocale();
	
	// Authentication initialization moved to +layout.svelte onMount
	// This prevents SSR errors on Vercel
	return {};
};