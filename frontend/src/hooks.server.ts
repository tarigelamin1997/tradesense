import type { Handle, HandleServerError } from '@sveltejs/kit';

// Add request handling with comprehensive logging
export const handle: Handle = async ({ event, resolve }) => {
	console.log(`[${new Date().toISOString()}] Handling request: ${event.request.method} ${event.url.pathname}`);
	
	try {
		// Log environment variables (without sensitive data)
		if (event.url.pathname === '/' || event.url.pathname.startsWith('/api')) {
			console.log('Environment check:', {
				NODE_ENV: process.env.NODE_ENV,
				VITE_API_URL_EXISTS: !!process.env.VITE_API_URL,
				PUBLIC_API_URL_EXISTS: !!process.env.PUBLIC_API_URL,
				DEPLOYMENT_URL: process.env.VERCEL_URL || 'not-on-vercel'
			});
		}
		
		const response = await resolve(event);
		return response;
	} catch (error) {
		console.error(`[${new Date().toISOString()}] Request error:`, error);
		throw error;
	}
};

export const handleError: HandleServerError = ({ error, event }) => {
	// Enhanced error logging
	const timestamp = new Date().toISOString();
	const errorId = Math.random().toString(36).substring(7);
	
	console.error(`[${timestamp}] Error ID: ${errorId}`);
	console.error('Request details:', {
		url: event.url.pathname,
		method: event.request.method,
		headers: Object.fromEntries(event.request.headers.entries()),
		platform: event.platform
	});
	
	// Log the full error
	if (error instanceof Error) {
		console.error('Error details:', {
			name: error.name,
			message: error.message,
			stack: error.stack,
			cause: error.cause
		});
	} else {
		console.error('Non-Error thrown:', error);
	}
	
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

	// Check for module import errors
	if (errorMessage.includes('Cannot find module') ||
		errorMessage.includes('Module not found')) {
		return {
			message: `Module import error: ${errorMessage}`,
			code: 'MODULE_NOT_FOUND'
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
		code: 'INTERNAL_ERROR',
		errorId // Include error ID for tracking
	};
};