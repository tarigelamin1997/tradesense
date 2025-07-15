

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export const universal = {
  "ssr": false
};
export const universal_id = "src/routes/login/+layout.ts";
export const imports = ["_app/immutable/nodes/2.BlBRxX2u.js","_app/immutable/chunks/Vx33HAo_.js","_app/immutable/chunks/M0oPezYK.js","_app/immutable/chunks/IHki7fMi.js"];
export const stylesheets = [];
export const fonts = [];
