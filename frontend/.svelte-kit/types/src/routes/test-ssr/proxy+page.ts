// @ts-nocheck
import type { PageLoad } from './$types';

export const load = async () => {
	// Simple load function that works both on server and client
	return {
		timestamp: new Date().toISOString(),
		message: 'This data was loaded successfully!'
	};
};;null as any as PageLoad;