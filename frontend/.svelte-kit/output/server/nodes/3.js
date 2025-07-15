

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/layout.svelte.js')).default;
export const universal = {
  "ssr": false
};
export const universal_id = "src/routes/register/+layout.ts";
export const imports = ["_app/immutable/nodes/3.BlBRxX2u.js","_app/immutable/chunks/Vx33HAo_.js","_app/immutable/chunks/M0oPezYK.js","_app/immutable/chunks/IHki7fMi.js"];
export const stylesheets = [];
export const fonts = [];
