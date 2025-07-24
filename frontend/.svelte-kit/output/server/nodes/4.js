import * as universal from '../entries/pages/register/_layout.ts.js';

export const index = 4;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/register/+layout.ts";
export const imports = ["_app/immutable/nodes/4.D6DKVHs5.js","_app/immutable/chunks/CHXW0M08.js","_app/immutable/chunks/BizRtQrO.js","_app/immutable/chunks/IHki7fMi.js"];
export const stylesheets = [];
export const fonts = [];
