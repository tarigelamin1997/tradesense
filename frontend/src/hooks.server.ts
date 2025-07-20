import type { HandleServerError } from '@sveltejs/kit';

export const handleError: HandleServerError = ({ error, event }) => {
	// Log the error for debugging
	console.error('Server error:', error);
	console.error('Request URL:', event.url.pathname);
	console.error('Request method:', event.request.method);
	
	// Extract useful error information
	const errorMessage = error instanceof Error ? error.message : 'Unknown error';
	const errorStack = error instanceof Error ? error.stack : '';
	
	// Check for common SSR issues
	if (errorMessage.includes('window is not defined') || 
		errorMessage.includes('document is not defined') ||
		errorMessage.includes('navigator is not defined') ||
		errorMessage.includes('localStorage is not defined')) {
		return {
			message: 'Server-side rendering error: Browser API accessed during SSR',
			code: 'SSR_BROWSER_API'
		};
	}
	
	if (errorMessage.includes('Cannot read properties of null') ||
		errorMessage.includes('Cannot read properties of undefined')) {
		return {
			message: 'Server-side rendering error: Null reference during SSR',
			code: 'SSR_NULL_REF'
		};
	}
	
	// Log critical errors (you might want to send these to a monitoring service)
	if (event.url.pathname.startsWith('/api/')) {
		console.error('API route error:', errorMessage);
	}
	
	// Return a generic error message to the client
	// Don't expose sensitive error details in production
	const isDev = process.env.NODE_ENV === 'development';
	return {
		message: isDev ? errorMessage : 'An unexpected error occurred',
		code: 'INTERNAL_ERROR'
	};
};