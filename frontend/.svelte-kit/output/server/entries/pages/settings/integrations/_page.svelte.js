import { c as create_ssr_component, v as validate_component, e as each, b as escape } from "../../../../chunks/ssr.js";
import { B as Breadcrumb } from "../../../../chunks/Breadcrumb.js";
import { L as Link, S as Settings_2, E as External_link } from "../../../../chunks/settings-2.js";
import { C as Check } from "../../../../chunks/check.js";
import { L as Loader_circle } from "../../../../chunks/loader-circle.js";
import { C as Circle_alert } from "../../../../chunks/circle-alert.js";
import { S as Shield } from "../../../../chunks/shield.js";
function formatLastSync(date) {
  if (!date) return "Never";
  const now = /* @__PURE__ */ new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 6e4);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} minutes ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hours ago`;
  return date.toLocaleDateString();
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let filteredIntegrations;
  let categories;
  let integrations = [
    {
      id: "interactive-brokers",
      name: "Interactive Brokers",
      description: "Connect your IBKR account for automatic trade imports and real-time data",
      category: "Broker",
      icon: "🏦",
      connected: true,
      lastSync: /* @__PURE__ */ new Date("2024-01-22T10:30:00"),
      features: ["Auto Import", "Real-time Data", "Portfolio Sync"]
    },
    {
      id: "td-ameritrade",
      name: "TD Ameritrade",
      description: "Sync your TDA/ThinkorSwim trades and portfolio data",
      category: "Broker",
      icon: "📈",
      connected: false,
      features: ["Trade Import", "Position Tracking", "Options Data"]
    },
    {
      id: "tradingview",
      name: "TradingView",
      description: "Import alerts and sync your watchlists with TradingView",
      category: "Analysis",
      icon: "📊",
      connected: false,
      features: ["Alert Import", "Watchlist Sync", "Chart Integration"]
    },
    {
      id: "discord",
      name: "Discord",
      description: "Send trade alerts and performance updates to Discord",
      category: "Notifications",
      icon: "💬",
      connected: true,
      lastSync: /* @__PURE__ */ new Date("2024-01-22T09:00:00"),
      features: ["Trade Alerts", "Daily Summary", "Custom Webhooks"]
    },
    {
      id: "google-sheets",
      name: "Google Sheets",
      description: "Export your trading data to Google Sheets for custom analysis",
      category: "Export",
      icon: "📑",
      connected: false,
      features: ["Auto Export", "Real-time Sync", "Custom Templates"]
    }
  ];
  let activeCategory = "all";
  let connecting = "";
  filteredIntegrations = integrations.filter((integration) => activeCategory === "all");
  categories = ["all", ...new Set(integrations.map((i) => i.category.toLowerCase()))];
  return `${$$result.head += `<!-- HEAD_svelte-3jezds_START -->${$$result.title = `<title>Integrations - Settings</title>`, ""}<meta name="description" content="Connect TradeSense with your favorite trading platforms and tools."><!-- HEAD_svelte-3jezds_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">${validate_component(Breadcrumb, "Breadcrumb").$$render($$result, {}, {}, {})} <div class="flex items-center gap-3 mt-4">${validate_component(Link, "Link").$$render(
    $$result,
    {
      class: "h-6 w-6 text-gray-600 dark:text-gray-400"
    },
    {},
    {}
  )} <div data-svelte-h="svelte-hn0y0m"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">Integrations</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Connect your favorite tools and platforms</p></div></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex gap-2 overflow-x-auto pb-2">${each(categories, (category) => {
    return `<button class="${"px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors " + escape(
      activeCategory === category ? "bg-blue-600 text-white" : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700",
      true
    )}">${escape(category.charAt(0).toUpperCase() + category.slice(1))} </button>`;
  })}</div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8"><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${each(filteredIntegrations, (integration) => {
    return `<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden"><div class="p-6"><div class="flex items-start justify-between mb-4"><div class="flex items-center gap-3"><span class="text-3xl">${escape(integration.icon)}</span> <div><h3 class="font-semibold text-gray-900 dark:text-white">${escape(integration.name)}</h3> <span class="text-xs text-gray-500 dark:text-gray-400 uppercase">${escape(integration.category)}</span> </div></div> ${integration.connected ? `<span class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">${validate_component(Check, "Check").$$render($$result, { class: "h-3 w-3" }, {}, {})}
									Connected
								</span>` : ``}</div> <p class="text-gray-600 dark:text-gray-400 text-sm mb-4">${escape(integration.description)}</p> <div class="space-y-2 mb-4">${each(integration.features, (feature) => {
      return `<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">${validate_component(Check, "Check").$$render($$result, { class: "h-3 w-3 text-green-500" }, {}, {})} ${escape(feature)} </div>`;
    })}</div> ${integration.connected && integration.lastSync ? `<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">Last synced: ${escape(formatLastSync(integration.lastSync))} </p>` : ``} <div class="flex gap-3"><button ${connecting === integration.id ? "disabled" : ""} class="${"flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors " + escape(
      integration.connected ? "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600" : "bg-blue-600 text-white hover:bg-blue-700",
      true
    )}">${connecting === integration.id ? `${validate_component(Loader_circle, "Loader2").$$render($$result, { class: "h-4 w-4 animate-spin" }, {}, {})} ${escape(integration.connected ? "Disconnecting..." : "Connecting...")}` : `${escape(integration.connected ? "Disconnect" : "Connect")}`}</button> ${integration.connected ? `<button class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">${validate_component(Settings_2, "Settings2").$$render($$result, { class: "h-5 w-5" }, {}, {})} </button>` : ``} </div></div> </div>`;
  })}</div>  <div class="mt-12 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6"><div class="flex items-start gap-4">${validate_component(Circle_alert, "AlertCircle").$$render(
    $$result,
    {
      class: "h-6 w-6 text-blue-600 dark:text-blue-400 shrink-0"
    },
    {},
    {}
  )} <div><h3 class="font-semibold text-gray-900 dark:text-white mb-2" data-svelte-h="svelte-1wnyto0">Need help with integrations?</h3> <p class="text-gray-600 dark:text-gray-400 mb-4" data-svelte-h="svelte-4yfqf5">Our integrations are designed to be secure and easy to set up. All connections use 
						industry-standard OAuth2 authentication and data is encrypted in transit.</p> <div class="flex flex-wrap gap-4"><a href="/docs/integrations" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline">View Integration Docs
							${validate_component(External_link, "ExternalLink").$$render($$result, { class: "h-4 w-4" }, {}, {})}</a> <a href="/support" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline">Contact Support
							${validate_component(External_link, "ExternalLink").$$render($$result, { class: "h-4 w-4" }, {}, {})}</a></div></div></div></div>  <div class="mt-6 flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">${validate_component(Shield, "Shield").$$render($$result, { class: "h-4 w-4" }, {}, {})} <p data-svelte-h="svelte-1dnual2">All integrations use secure OAuth2 authentication. We never store your passwords.</p></div></div></div>`;
});
export {
  Page as default
};
