

export const index = 7;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/debug/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/7.f2JlxjT1.js","_app/immutable/chunks/M0oPezYK.js","_app/immutable/chunks/IHki7fMi.js"];
export const stylesheets = [];
export const fonts = [];
