import * as server from '../entries/pages/dashboard/_page.server.ts.js';

export const index = 25;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/dashboard/_page.svelte.js')).default;
export { server };
export const server_id = "src/routes/dashboard/+page.server.ts";
export const imports = ["_app/immutable/nodes/25.CgEiY_Tp.js","_app/immutable/chunks/BizRtQrO.js","_app/immutable/chunks/CEysSNcE.js","_app/immutable/chunks/IHki7fMi.js","_app/immutable/chunks/CMDLyNOv.js","_app/immutable/chunks/Bt-Xh7oU.js","_app/immutable/chunks/QuJ8ahAQ.js","_app/immutable/chunks/Y7kOa4Iv.js","_app/immutable/chunks/n4AE9yzk.js","_app/immutable/chunks/skAg_FJw.js","_app/immutable/chunks/BcaM5LJ_.js","_app/immutable/chunks/f2duTv6Z.js","_app/immutable/chunks/D0QH3NT1.js","_app/immutable/chunks/DVqflHuo.js","_app/immutable/chunks/mkWhIWP_.js","_app/immutable/chunks/q8God5cf.js","_app/immutable/chunks/D7XzsqTY.js","_app/immutable/chunks/-74CPqXK.js","_app/immutable/chunks/C1FmrZbK.js","_app/immutable/chunks/upEiMeBx.js","_app/immutable/chunks/ixuYbyiU.js","_app/immutable/chunks/MuiY7nbG.js","_app/immutable/chunks/CgUbR3dA.js","_app/immutable/chunks/KWZs6rA_.js","_app/immutable/chunks/fruAf-Ay.js","_app/immutable/chunks/CNsmtZI0.js","_app/immutable/chunks/BaXaLpMJ.js","_app/immutable/chunks/BQ62-GnZ.js","_app/immutable/chunks/CyWvydgK.js","_app/immutable/chunks/Cpj98o6Y.js"];
export const stylesheets = ["_app/immutable/assets/MetricCard.BhuE9Yks.css","_app/immutable/assets/TradeList.DeT4s5Q3.css","_app/immutable/assets/FeatureGate.C4VzDzx_.css","_app/immutable/assets/TradeInsights.CbSTnkLr.css","_app/immutable/assets/LoadingSkeleton.ESvKeOUR.css","_app/immutable/assets/25.B4Lh6ggn.css"];
export const fonts = [];
