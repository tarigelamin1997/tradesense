import { c as create_ssr_component, v as validate_component, e as each, b as escape } from "../../../../chunks/ssr.js";
import { K as Key } from "../../../../chunks/key.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { C as Calendar } from "../../../../chunks/calendar.js";
import { A as Activity, E as Eye_off, C as Copy } from "../../../../chunks/eye-off.js";
import { T as Trash_2 } from "../../../../chunks/trash-2.js";
import { E as Eye } from "../../../../chunks/eye.js";
import { S as Shield } from "../../../../chunks/shield.js";
function formatDate(date) {
  if (!date) return "Never";
  return date.toLocaleDateString();
}
function maskKey(key) {
  return key.substring(0, 10) + "..." + key.substring(key.length - 4);
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let apiKeys = [
    {
      id: "1",
      name: "Production API",
      key: "sk_live_...abc123",
      lastUsed: /* @__PURE__ */ new Date("2024-01-22T10:00:00"),
      created: /* @__PURE__ */ new Date("2024-01-01"),
      permissions: ["read:trades", "write:trades", "read:analytics"],
      requestCount: 1234
    },
    {
      id: "2",
      name: "Testing Key",
      key: "sk_test_...xyz789",
      lastUsed: null,
      created: /* @__PURE__ */ new Date("2024-01-15"),
      permissions: ["read:trades"],
      requestCount: 0
    }
  ];
  let showKey = {};
  let copied = "";
  return `${$$result.head += `<!-- HEAD_svelte-ds2xwb_START -->${$$result.title = `<title>API Keys - Settings</title>`, ""}<meta name="description" content="Manage your TradeSense API keys for third-party integrations."><!-- HEAD_svelte-ds2xwb_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex items-center justify-between"><div class="flex items-center gap-3">${validate_component(Key, "Key").$$render(
    $$result,
    {
      class: "h-6 w-6 text-gray-600 dark:text-gray-400"
    },
    {},
    {}
  )} <div data-svelte-h="svelte-fvtvw8"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">API Keys</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Manage access to your TradeSense data via API</p></div></div> <button class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">${validate_component(Plus, "Plus").$$render($$result, { class: "h-5 w-5" }, {}, {})}
					Create New Key</button></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">${apiKeys.length === 0 ? `<div class="bg-white dark:bg-gray-800 rounded-lg p-12 text-center">${validate_component(Key, "Key").$$render(
    $$result,
    {
      class: "h-12 w-12 text-gray-400 mx-auto mb-4"
    },
    {},
    {}
  )} <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2" data-svelte-h="svelte-11s9lnl">No API keys yet</h3> <p class="text-gray-600 dark:text-gray-400 mb-6" data-svelte-h="svelte-imtq3b">Create your first API key to start integrating with TradeSense.</p> <button class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">${validate_component(Plus, "Plus").$$render($$result, { class: "h-5 w-5" }, {}, {})}
					Create Your First Key</button></div>` : `<div class="space-y-4">${each(apiKeys, (apiKey) => {
    return `<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><div class="flex items-start justify-between mb-4"><div><h3 class="text-lg font-semibold text-gray-900 dark:text-white">${escape(apiKey.name)}</h3> <div class="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400"><span class="flex items-center gap-1">${validate_component(Calendar, "Calendar").$$render($$result, { class: "h-4 w-4" }, {}, {})}
										Created ${escape(formatDate(apiKey.created))}</span> <span class="flex items-center gap-1">${validate_component(Activity, "Activity").$$render($$result, { class: "h-4 w-4" }, {}, {})} ${escape(apiKey.requestCount)} requests</span> <span>Last used: ${escape(formatDate(apiKey.lastUsed))}</span> </div></div> <button class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300">${validate_component(Trash_2, "Trash2").$$render($$result, { class: "h-5 w-5" }, {}, {})} </button></div>  <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4"><div class="flex items-center justify-between"><code class="font-mono text-sm text-gray-900 dark:text-white">${escape(showKey[apiKey.id] ? apiKey.key : maskKey(apiKey.key))}</code> <div class="flex items-center gap-2"><button class="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">${showKey[apiKey.id] ? `${validate_component(Eye_off, "EyeOff").$$render($$result, { class: "h-4 w-4" }, {}, {})}` : `${validate_component(Eye, "Eye").$$render($$result, { class: "h-4 w-4" }, {}, {})}`}</button> <button class="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">${copied === apiKey.id ? `${validate_component(Check, "Check").$$render($$result, { class: "h-4 w-4 text-green-600" }, {}, {})}` : `${validate_component(Copy, "Copy").$$render($$result, { class: "h-4 w-4" }, {}, {})}`} </button></div> </div></div>  <div><p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-sc3rz5">Permissions:</p> <div class="flex flex-wrap gap-2">${each(apiKey.permissions, (permission) => {
      return `<span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md">${escape(permission)} </span>`;
    })} </div></div> </div>`;
  })}</div>`}  <div class="mt-8 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6" data-svelte-h="svelte-1j2pn2r"><h3 class="font-semibold text-gray-900 dark:text-white mb-3">Getting Started with the API</h3> <p class="text-gray-600 dark:text-gray-400 mb-4">Use your API keys to integrate TradeSense with your applications and workflows.</p> <div class="space-y-3"><div class="font-mono text-sm bg-gray-100 dark:bg-gray-800 p-3 rounded"><p class="text-gray-500 dark:text-gray-400 mb-1"># Example API request</p> <p class="text-gray-900 dark:text-white">curl -H &quot;Authorization: Bearer YOUR_API_KEY&quot; \\</p> <p class="text-gray-900 dark:text-white ml-4">https://api.tradesense.com/v1/trades</p></div> <a href="/docs/api" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline">View API Documentation →</a></div></div>  <div class="mt-6 flex items-start gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">${validate_component(Shield, "Shield").$$render(
    $$result,
    {
      class: "h-5 w-5 text-yellow-600 dark:text-yellow-400 shrink-0 mt-0.5"
    },
    {},
    {}
  )} <div class="text-sm text-yellow-800 dark:text-yellow-200" data-svelte-h="svelte-1b4sv0h"><p class="font-medium mb-1">Keep your API keys secure</p> <p>Never share your API keys publicly or commit them to version control. Treat them like passwords.</p></div></div></div>  ${``}  ${``}</div>`;
});
export {
  Page as default
};
