import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock SvelteKit modules
vi.mock('$app/navigation', () => ({
	goto: vi.fn(),
	invalidate: vi.fn(),
	invalidateAll: vi.fn(),
	beforeNavigate: vi.fn(),
	afterNavigate: vi.fn()
}));

vi.mock('$app/stores', () => {
	const page = {
		subscribe: vi.fn((cb) => {
			cb({
				url: new URL('http://localhost'),
				params: {},
				route: {
					id: '/'
				},
				status: 200,
				error: null,
				data: {},
				form: null
			});
			return () => {};
		})
	};

	const navigating = {
		subscribe: vi.fn((cb) => {
			cb(null);
			return () => {};
		})
	};

	const updated = {
		subscribe: vi.fn((cb) => {
			cb(false);
			return () => {};
		}),
		check: vi.fn()
	};

	return {
		page,
		navigating,
		updated
	};
});

vi.mock('$app/environment', () => ({
	browser: true,
	dev: true,
	building: false,
	version: 'test'
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
	writable: true,
	value: vi.fn().mockImplementation((query) => ({
		matches: false,
		media: query,
		onchange: null,
		addListener: vi.fn(),
		removeListener: vi.fn(),
		addEventListener: vi.fn(),
		removeEventListener: vi.fn(),
		dispatchEvent: vi.fn()
	}))
});

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn()
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
	observe: vi.fn(),
	unobserve: vi.fn(),
	disconnect: vi.fn()
}));