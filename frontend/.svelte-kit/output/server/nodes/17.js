

export const index = 17;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/trades/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/17.B0Mj9et1.js","_app/immutable/chunks/M0oPezYK.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/D2lGS4wI.js"];
export const stylesheets = [];
export const fonts = [];
