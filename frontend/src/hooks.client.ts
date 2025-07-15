import type { HandleClientError } from '@sveltejs/kit';
import { logger } from '$lib/utils/logger';

export const handleError: HandleClientError = ({ error, event }) => {
	logger.error('Client error:', error);
	logger.error('Error details:', {
		message: error instanceof Error ? error.message : 'Unknown error',
		stack: error instanceof Error ? error.stack : undefined,
		url: event.url.href
	});
	return {
		message: 'An unexpected error occurred'
	};
};