import { s as subscribe } from "../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, e as each, b as escape, a as add_attribute, m as missing_component } from "../../chunks/ssr.js";
import { p as page } from "../../chunks/stores.js";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/state.svelte.js";
import { F as File_question_mark, S as Server_crash } from "../../chunks/server-crash.js";
import { T as Triangle_alert } from "../../chunks/triangle-alert.js";
import { S as Search } from "../../chunks/search.js";
import { A as Arrow_left } from "../../chunks/arrow-left.js";
import { H as House } from "../../chunks/house.js";
const Error = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let error;
  let status;
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  const publicPages = [
    { path: "/", label: "Home", icon: House },
    { path: "/features", label: "Features" },
    { path: "/pricing", label: "Pricing" },
    { path: "/about", label: "About" },
    { path: "/blog", label: "Blog" },
    { path: "/contact", label: "Contact" },
    { path: "/docs", label: "Documentation" }
  ];
  const authPages = [
    { path: "/dashboard", label: "Dashboard" },
    { path: "/trades", label: "Trade Log" },
    { path: "/portfolio", label: "Portfolio" },
    { path: "/analytics", label: "Analytics" },
    { path: "/journal", label: "Journal" },
    {
      path: "/ai-insights",
      label: "AI Insights"
    }
  ];
  const supportPages = [
    {
      path: "/support",
      label: "Support Center"
    },
    {
      path: "/support/kb",
      label: "Knowledge Base"
    },
    { path: "/status", label: "System Status" }
  ];
  error = $page.error;
  status = $page.status;
  $$unsubscribe_page();
  return `<div class="min-h-screen bg-gray-50 dark:bg-gray-900"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">${status === 404 ? ` <div class="text-center"><div class="flex justify-center mb-8"><div class="relative">${validate_component(File_question_mark, "FileQuestion").$$render(
    $$result,
    {
      class: "h-24 w-24 text-gray-400 dark:text-gray-600"
    },
    {},
    {}
  )} <div class="absolute -bottom-2 -right-2 bg-yellow-500 rounded-full p-2">${validate_component(Triangle_alert, "AlertTriangle").$$render($$result, { class: "h-6 w-6 text-white" }, {}, {})}</div></div></div> <h1 class="text-6xl font-bold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-bk3d2s">404</h1> <h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-4" data-svelte-h="svelte-3alolz">Page Not Found</h2> <p class="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto" data-svelte-h="svelte-uwjox3">Sorry, we couldn&#39;t find the page you&#39;re looking for. It might have been moved, 
					deleted, or the URL might be incorrect.</p>  <div class="max-w-md mx-auto mb-12"><form class="relative"><input type="text" name="search" placeholder="Search for pages..." class="w-full px-4 py-3 pr-12 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"> <button type="submit" class="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">${validate_component(Search, "Search").$$render($$result, { class: "h-5 w-5" }, {}, {})}</button></form></div>  <div class="flex flex-wrap justify-center gap-4 mb-12"><button class="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors">${validate_component(Arrow_left, "ArrowLeft").$$render($$result, { class: "h-4 w-4" }, {}, {})}
						Go Back</button> <a href="/" class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">${validate_component(House, "Home").$$render($$result, { class: "h-4 w-4" }, {}, {})}
						Go to Home</a></div>  <div class="border-t border-gray-200 dark:border-gray-800 pt-12"><h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-8" data-svelte-h="svelte-mschcp">Here are some pages you might be looking for:</h3> <div class="grid md:grid-cols-3 gap-8 text-left max-w-4xl mx-auto"> <div><h4 class="font-medium text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-7e5ol6">General</h4> <ul class="space-y-2">${each(publicPages, (page2) => {
    return `<li><a${add_attribute("href", page2.path, 0)} class="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2">${page2.icon ? `${validate_component(page2.icon || missing_component, "svelte:component").$$render($$result, { class: "h-4 w-4" }, {}, {})}` : ``} ${escape(page2.label)}</a> </li>`;
  })}</ul></div>  <div><h4 class="font-medium text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-1f7ihf6">Trading Platform</h4> <ul class="space-y-2">${each(authPages, (page2) => {
    return `<li><a${add_attribute("href", page2.path, 0)} class="text-blue-600 dark:text-blue-400 hover:underline">${escape(page2.label)}</a> </li>`;
  })}</ul></div>  <div><h4 class="font-medium text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-1p4ugf0">Help &amp; Support</h4> <ul class="space-y-2">${each(supportPages, (page2) => {
    return `<li><a${add_attribute("href", page2.path, 0)} class="text-blue-600 dark:text-blue-400 hover:underline">${escape(page2.label)}</a> </li>`;
  })}</ul></div></div></div></div>` : `${status === 500 ? ` <div class="text-center"><div class="flex justify-center mb-8"><div class="relative">${validate_component(Server_crash, "ServerCrash").$$render($$result, { class: "h-24 w-24 text-red-500" }, {}, {})}</div></div> <h1 class="text-6xl font-bold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-q6nh9l">500</h1> <h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-4" data-svelte-h="svelte-10d266z">Internal Server Error</h2> <p class="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto" data-svelte-h="svelte-10ot2xz">Something went wrong on our end. We&#39;re working to fix it. 
					Please try again in a few moments.</p> <div class="flex flex-wrap justify-center gap-4"><button class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors" data-svelte-h="svelte-bwmpai">Try Again</button> <a href="/" class="px-6 py-3 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors" data-svelte-h="svelte-qg4wpd">Go to Home</a></div> ${error?.message ? `<div class="mt-8 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg max-w-2xl mx-auto"><p class="text-sm text-red-600 dark:text-red-400">Error details: ${escape(error.message)}</p></div>` : ``}</div>` : ` <div class="text-center"><div class="flex justify-center mb-8">${validate_component(Triangle_alert, "AlertTriangle").$$render($$result, { class: "h-24 w-24 text-yellow-500" }, {}, {})}</div> <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-l5ihmw">Oops! Something went wrong</h1> <p class="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto" data-svelte-h="svelte-1w2x39t">An unexpected error occurred. Please try again or contact support if the problem persists.</p> <div class="flex flex-wrap justify-center gap-4"><button class="px-6 py-3 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors" data-svelte-h="svelte-m9ugbh">Go Back</button> <a href="/support" class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors" data-svelte-h="svelte-xk7i0n">Contact Support</a></div></div>`}`}</div> </div>`;
});
export {
  Error as default
};
