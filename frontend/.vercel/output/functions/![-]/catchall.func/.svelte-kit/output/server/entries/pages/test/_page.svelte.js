import { c as create_ssr_component, d as escape } from "../../../chunks/ssr.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let status = "Testing axios...";
  return `<h1 data-svelte-h="svelte-rcdvs6">Axios Test</h1> <p>${escape(status)}</p>`;
});
export {
  Page as default
};
