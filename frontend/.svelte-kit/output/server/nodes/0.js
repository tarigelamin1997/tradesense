import * as universal from '../entries/pages/_layout.ts.js';

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export { universal };
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.BUoRaLc8.js","_app/immutable/chunks/UAPnr0-D.js","_app/immutable/chunks/Bav7U_R_.js","_app/immutable/chunks/Dq7h7Pqt.js","_app/immutable/chunks/D2lGS4wI.js","_app/immutable/chunks/M0oPezYK.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/0yqR112t.js","_app/immutable/chunks/Ck4FRYpq.js","_app/immutable/chunks/DSTCGpCL.js","_app/immutable/chunks/RLz4a98-.js","_app/immutable/chunks/9oHaGlV1.js","_app/immutable/chunks/k_TuXpN0.js","_app/immutable/chunks/Cqm7eHgy.js","_app/immutable/chunks/sSn3OGFc.js","_app/immutable/chunks/zhUnpIM1.js","_app/immutable/chunks/CVXI2qhL.js","_app/immutable/chunks/DwzRa6LX.js"];
export const stylesheets = ["_app/immutable/assets/0.BhLJUsDe.css"];
export const fonts = [];
