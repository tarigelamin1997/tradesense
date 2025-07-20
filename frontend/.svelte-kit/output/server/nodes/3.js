import * as universal from '../entries/pages/login/_layout.ts.js';

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/login/+layout.ts";
export const imports = ["_app/immutable/nodes/3.mPRnIGzx.js","_app/immutable/chunks/Dr3zLGzD.js","_app/immutable/chunks/Lbc7qOuA.js","_app/immutable/chunks/IHki7fMi.js"];
export const stylesheets = [];
export const fonts = [];
