import { c as create_ssr_component, d as escape } from "../../../chunks/ssr.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let status = "Loading...";
  let details = {};
  return `<div style="padding: 2rem;"><h1 data-svelte-h="svelte-8m2oq2">Debug Page</h1> <p>Status: ${escape(status)}</p> <pre>${escape(JSON.stringify(details, null, 2))}</pre> <h2 data-svelte-h="svelte-o200j1">Navigation Links</h2> <ul data-svelte-h="svelte-fnwqli"><li><a href="/">Home</a></li> <li><a href="/login">Login</a></li> <li><a href="/register">Register</a></li> <li><a href="/tradelog">Trade Log</a></li></ul></div>`;
});
export {
  Page as default
};
