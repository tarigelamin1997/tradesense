

export const index = 30;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/register/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/30.DDnv2zgu.js","_app/immutable/chunks/Lbc7qOuA.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/COKI2rXe.js"];
export const stylesheets = ["_app/immutable/assets/30.Br04dzim.css"];
export const fonts = [];
