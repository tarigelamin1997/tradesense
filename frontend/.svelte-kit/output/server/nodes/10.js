

export const index = 10;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/payment-success/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/10.5Vg4ziHZ.js","_app/immutable/chunks/M0oPezYK.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/D2lGS4wI.js","_app/immutable/chunks/DwzRa6LX.js","_app/immutable/chunks/Ck4FRYpq.js","_app/immutable/chunks/DSTCGpCL.js","_app/immutable/chunks/CyreFHQC.js"];
export const stylesheets = ["_app/immutable/assets/10.B-NdzV42.css"];
export const fonts = [];
