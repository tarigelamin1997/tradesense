// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
import type { AuthUser } from '$lib/server/auth';

declare global {
	namespace App {
		interface Error {
			code?: string;
			errorId?: string;
		}
		
		interface Locals {
			authToken: string | null;
			user: AuthUser | null;
			isAuthenticated: boolean;
		}
		
		interface PageData {
			user?: AuthUser | null;
		}
		
		// interface Platform {}
	}
}

export {};