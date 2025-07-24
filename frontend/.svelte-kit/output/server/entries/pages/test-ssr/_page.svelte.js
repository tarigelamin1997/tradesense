import { c as create_ssr_component, b as escape } from "../../../chunks/ssr.js";
import { b as browser } from "../../../chunks/index2.js";
const css = {
  code: "h1.svelte-1jzo0qo{color:#333;margin-bottom:1rem}ul.svelte-1jzo0qo{background:#f5f5f5;padding:1rem;border-radius:4px;list-style-type:none}li.svelte-1jzo0qo{margin:0.5rem 0;font-family:monospace}",
  map: '{"version":3,"file":"+page.svelte","sources":["+page.svelte"],"sourcesContent":["<script lang=\\"ts\\">\\"use strict\\";\\nimport { browser } from \\"$app/environment\\";\\nconst renderTime = (/* @__PURE__ */ new Date()).toISOString();\\nconst isBrowser = browser;\\n<\/script>\\n\\n<h1>SSR Test Page</h1>\\n<p>This page tests if basic SSR is working on Vercel.</p>\\n\\n<ul>\\n\\t<li>Rendered at: {renderTime}</li>\\n\\t<li>Is browser: {isBrowser}</li>\\n\\t<li>Environment: {import.meta.env.MODE}</li>\\n</ul>\\n\\n<p>If you can see this page, basic SSR is working!</p>\\n\\n<style>\\n\\th1 {\\n\\t\\tcolor: #333;\\n\\t\\tmargin-bottom: 1rem;\\n\\t}\\n\\t\\n\\tul {\\n\\t\\tbackground: #f5f5f5;\\n\\t\\tpadding: 1rem;\\n\\t\\tborder-radius: 4px;\\n\\t\\tlist-style-type: none;\\n\\t}\\n\\t\\n\\tli {\\n\\t\\tmargin: 0.5rem 0;\\n\\t\\tfont-family: monospace;\\n\\t}\\n</style>"],"names":[],"mappings":"AAkBC,iBAAG,CACF,KAAK,CAAE,IAAI,CACX,aAAa,CAAE,IAChB,CAEA,iBAAG,CACF,UAAU,CAAE,OAAO,CACnB,OAAO,CAAE,IAAI,CACb,aAAa,CAAE,GAAG,CAClB,eAAe,CAAE,IAClB,CAEA,iBAAG,CACF,MAAM,CAAE,MAAM,CAAC,CAAC,CAChB,WAAW,CAAE,SACd"}'
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const renderTime = /* @__PURE__ */ (/* @__PURE__ */ new Date()).toISOString();
  const isBrowser = browser;
  $$result.css.add(css);
  return `<h1 class="svelte-1jzo0qo" data-svelte-h="svelte-izq0uj">SSR Test Page</h1> <p data-svelte-h="svelte-ohnqqk">This page tests if basic SSR is working on Vercel.</p> <ul class="svelte-1jzo0qo"><li class="svelte-1jzo0qo">Rendered at: ${escape(renderTime)}</li> <li class="svelte-1jzo0qo">Is browser: ${escape(isBrowser)}</li> <li class="svelte-1jzo0qo">Environment: ${escape("production")}</li></ul> <p data-svelte-h="svelte-1j410ue">If you can see this page, basic SSR is working!</p>`;
});
export {
  Page as default
};
