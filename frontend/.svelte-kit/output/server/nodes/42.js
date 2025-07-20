

export const index = 42;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/trades/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/42.dlSG1my5.js","_app/immutable/chunks/Lbc7qOuA.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/_pMazo4M.js"];
export const stylesheets = [];
export const fonts = [];
