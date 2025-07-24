import { c as create_ssr_component, v as validate_component, e as each, a as add_attribute, b as escape, m as missing_component } from "../../../../chunks/ssr.js";
import { S as Save, D as Database } from "../../../../chunks/save.js";
import { S as Settings } from "../../../../chunks/settings.js";
import { S as Shield } from "../../../../chunks/shield.js";
import { M as Mail } from "../../../../chunks/mail.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { G as Globe } from "../../../../chunks/globe.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let activeTab = "general";
  let settings = {
    general: {
      siteName: "TradeSense",
      siteUrl: "https://tradesense.com",
      contactEmail: "support@tradesense.com",
      maintenanceMode: false
    }
  };
  const tabs = [
    {
      id: "general",
      label: "General",
      icon: Settings
    },
    {
      id: "security",
      label: "Security",
      icon: Shield
    },
    { id: "email", label: "Email", icon: Mail },
    { id: "api", label: "API", icon: Zap },
    {
      id: "features",
      label: "Features",
      icon: Globe
    },
    {
      id: "integrations",
      label: "Integrations",
      icon: Database
    }
  ];
  return `${$$result.head += `<!-- HEAD_svelte-h6t456_START -->${$$result.title = `<title>System Settings - Admin Dashboard</title>`, ""}<!-- HEAD_svelte-h6t456_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex items-center justify-between"><div data-svelte-h="svelte-102g5ha"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">System Settings</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Configure platform-wide settings and features</p></div> <button ${""} class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">${`${validate_component(Save, "Save").$$render($$result, { class: "h-4 w-4" }, {}, {})}`}
					Save Changes</button></div></div></div>  ${``}  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"><div class="lg:grid lg:grid-cols-4 lg:gap-8"> <nav class="mb-8 lg:mb-0"><ul class="space-y-1">${each(tabs, (tab) => {
    return `<li><button class="${"w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors " + escape(
      activeTab === tab.id ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400" : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800",
      true
    )}">${validate_component(tab.icon || missing_component, "svelte:component").$$render($$result, { class: "h-5 w-5" }, {}, {})} ${escape(tab.label)}</button> </li>`;
  })}</ul></nav>  <div class="lg:col-span-3"><div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">${`<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6" data-svelte-h="svelte-141uq53">General Settings</h2> <div class="space-y-6"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1yz52cy">Site Name</label> <input type="text" class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"${add_attribute("value", settings.general.siteName, 0)}></div> <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-2awnx6">Site URL</label> <input type="url" class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"${add_attribute("value", settings.general.siteUrl, 0)}></div> <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1w5emh4">Contact Email</label> <input type="email" class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"${add_attribute("value", settings.general.contactEmail, 0)}></div> <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1dd0980">Default Timezone</label> <select class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"><option value="America/New_York" data-svelte-h="svelte-104n62y">Eastern Time</option><option value="America/Chicago" data-svelte-h="svelte-ftk6cp">Central Time</option><option value="America/Denver" data-svelte-h="svelte-17d8ddf">Mountain Time</option><option value="America/Los_Angeles" data-svelte-h="svelte-7r605v">Pacific Time</option><option value="UTC" data-svelte-h="svelte-1c5kwym">UTC</option></select></div> <div class="flex items-center gap-3"><input type="checkbox" id="maintenance" class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", settings.general.maintenanceMode, 1)}> <label for="maintenance" class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-144pjxi">Enable Maintenance Mode</label></div></div>`}</div></div></div></div></div>`;
});
export {
  Page as default
};
