// Allow SSR for register page - our SSR-safe API client handles this now
// Removing ssr = false to fix Vercel deployment
export const prerender = false;