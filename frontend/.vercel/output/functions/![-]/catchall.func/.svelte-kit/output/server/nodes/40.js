import * as universal from '../entries/pages/test-ssr/_page.ts.js';

export const index = 40;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/test-ssr/_page.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/test-ssr/+page.ts";
export const imports = ["_app/immutable/nodes/40.COmB3Ak-.js","_app/immutable/chunks/Lbc7qOuA.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/Bt-Xh7oU.js"];
export const stylesheets = ["_app/immutable/assets/40.okE2dYN4.css"];
export const fonts = [];
