import { s as subscribe } from "./utils.js";
import { c as create_ssr_component, v as validate_component, e as each, a as add_attribute, b as escape } from "./ssr.js";
import { p as page } from "./stores.js";
import { H as House } from "./house.js";
import { C as Chevron_right } from "./chevron-right.js";
const css = {
  code: "nav.svelte-1evb1ao{flex-wrap:wrap}@media(max-width: 640px){nav.svelte-1evb1ao{font-size:0.75rem;line-height:1rem}}",
  map: `{"version":3,"file":"Breadcrumb.svelte","sources":["Breadcrumb.svelte"],"sourcesContent":["<script lang=\\"ts\\">\\"use strict\\";\\nimport { ChevronRight, Home } from \\"lucide-svelte\\";\\nimport { page } from \\"$app/stores\\";\\nexport let items = [];\\nexport let showHome = true;\\n$: autoItems = items.length > 0 ? items : generateFromPath($page.url.pathname);\\nfunction generateFromPath(pathname) {\\n  const segments = pathname.split(\\"/\\").filter(Boolean);\\n  const breadcrumbs = [];\\n  segments.forEach((segment, index) => {\\n    const href = \\"/\\" + segments.slice(0, index + 1).join(\\"/\\");\\n    const label = segment.split(\\"-\\").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(\\" \\");\\n    breadcrumbs.push({\\n      label,\\n      href: index < segments.length - 1 ? href : void 0\\n    });\\n  });\\n  return breadcrumbs;\\n}\\n<\/script>\\n\\n<nav aria-label=\\"Breadcrumb\\" class=\\"flex items-center space-x-2 text-sm\\">\\n\\t{#if showHome}\\n\\t\\t<a \\n\\t\\t\\thref=\\"/\\" \\n\\t\\t\\tclass=\\"text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors\\"\\n\\t\\t\\taria-label=\\"Home\\"\\n\\t\\t>\\n\\t\\t\\t<Home class=\\"h-4 w-4\\" />\\n\\t\\t</a>\\n\\t\\t{#if autoItems.length > 0}\\n\\t\\t\\t<ChevronRight class=\\"h-4 w-4 text-gray-400 dark:text-gray-600\\" />\\n\\t\\t{/if}\\n\\t{/if}\\n\\t\\n\\t{#each autoItems as item, index}\\n\\t\\t{#if item.href}\\n\\t\\t\\t<a \\n\\t\\t\\t\\thref={item.href}\\n\\t\\t\\t\\tclass=\\"text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors\\"\\n\\t\\t\\t>\\n\\t\\t\\t\\t{item.label}\\n\\t\\t\\t</a>\\n\\t\\t{:else}\\n\\t\\t\\t<span class=\\"text-gray-900 dark:text-white font-medium\\">\\n\\t\\t\\t\\t{item.label}\\n\\t\\t\\t</span>\\n\\t\\t{/if}\\n\\t\\t\\n\\t\\t{#if index < autoItems.length - 1}\\n\\t\\t\\t<ChevronRight class=\\"h-4 w-4 text-gray-400 dark:text-gray-600\\" />\\n\\t\\t{/if}\\n\\t{/each}\\n</nav>\\n\\n<style>\\n\\t/* Ensure breadcrumb doesn't wrap on small screens */\\n\\tnav {\\n\\t\\tflex-wrap: wrap;\\n\\t}\\n\\t\\n\\t@media (max-width: 640px) {\\n\\t\\tnav {\\n\\t\\t\\tfont-size: 0.75rem;\\n\\t\\t\\tline-height: 1rem;\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"AAyDC,kBAAI,CACH,SAAS,CAAE,IACZ,CAEA,MAAO,YAAY,KAAK,CAAE,CACzB,kBAAI,CACH,SAAS,CAAE,OAAO,CAClB,WAAW,CAAE,IACd,CACD"}`
};
function generateFromPath(pathname) {
  const segments = pathname.split("/").filter(Boolean);
  const breadcrumbs = [];
  segments.forEach((segment, index) => {
    const href = "/" + segments.slice(0, index + 1).join("/");
    const label = segment.split("-").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
    breadcrumbs.push({
      label,
      href: index < segments.length - 1 ? href : void 0
    });
  });
  return breadcrumbs;
}
const Breadcrumb = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let autoItems;
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let { items = [] } = $$props;
  let { showHome = true } = $$props;
  if ($$props.items === void 0 && $$bindings.items && items !== void 0) $$bindings.items(items);
  if ($$props.showHome === void 0 && $$bindings.showHome && showHome !== void 0) $$bindings.showHome(showHome);
  $$result.css.add(css);
  autoItems = items.length > 0 ? items : generateFromPath($page.url.pathname);
  $$unsubscribe_page();
  return `<nav aria-label="Breadcrumb" class="flex items-center space-x-2 text-sm svelte-1evb1ao">${showHome ? `<a href="/" class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors" aria-label="Home">${validate_component(House, "Home").$$render($$result, { class: "h-4 w-4" }, {}, {})}</a> ${autoItems.length > 0 ? `${validate_component(Chevron_right, "ChevronRight").$$render(
    $$result,
    {
      class: "h-4 w-4 text-gray-400 dark:text-gray-600"
    },
    {},
    {}
  )}` : ``}` : ``} ${each(autoItems, (item, index) => {
    return `${item.href ? `<a${add_attribute("href", item.href, 0)} class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors">${escape(item.label)} </a>` : `<span class="text-gray-900 dark:text-white font-medium">${escape(item.label)} </span>`} ${index < autoItems.length - 1 ? `${validate_component(Chevron_right, "ChevronRight").$$render(
      $$result,
      {
        class: "h-4 w-4 text-gray-400 dark:text-gray-600"
      },
      {},
      {}
    )}` : ``}`;
  })} </nav>`;
});
export {
  Breadcrumb as B
};
