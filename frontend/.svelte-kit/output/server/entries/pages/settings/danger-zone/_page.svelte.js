import { c as create_ssr_component, v as validate_component, e as each, b as escape, m as missing_component, a as add_attribute } from "../../../../chunks/ssr.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/state.svelte.js";
import { L as LoadingSpinner } from "../../../../chunks/LoadingSpinner.js";
import { T as Triangle_alert } from "../../../../chunks/triangle-alert.js";
import { S as Shield } from "../../../../chunks/shield.js";
import { D as Download } from "../../../../chunks/download.js";
import { A as Archive } from "../../../../chunks/archive.js";
import { T as Trash_2 } from "../../../../chunks/trash-2.js";
import { X } from "../../../../chunks/x.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let showDeleteModal = false;
  let showDeactivateModal = false;
  let deleteConfirmation = "";
  let loading = false;
  const dangerousActions = [
    {
      id: "export",
      title: "Export All Data",
      description: "Download all your data before making any destructive changes",
      icon: Download,
      action: exportAllData,
      variant: "warning"
    },
    {
      id: "archive",
      title: "Archive Account",
      description: "Temporarily disable your account. You can reactivate it anytime.",
      icon: Archive,
      action: () => showDeactivateModal = true,
      variant: "warning"
    },
    {
      id: "delete",
      title: "Delete Account",
      description: "Permanently delete your account and all associated data. This cannot be undone.",
      icon: Trash_2,
      action: () => showDeleteModal = true,
      variant: "danger"
    }
  ];
  async function exportAllData() {
    loading = true;
    await new Promise((resolve) => setTimeout(resolve, 2e3));
    loading = false;
    console.log("Exporting all data...");
  }
  return `${$$result.head += `<!-- HEAD_svelte-1kmn6xq_START -->${$$result.title = `<title>Danger Zone - Settings</title>`, ""}<meta name="description" content="Manage sensitive account actions for your TradeSense account."><!-- HEAD_svelte-1kmn6xq_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex items-center gap-3"><div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">${validate_component(Triangle_alert, "AlertTriangle").$$render(
    $$result,
    {
      class: "h-6 w-6 text-red-600 dark:text-red-400"
    },
    {},
    {}
  )}</div> <div data-svelte-h="svelte-1hk1czn"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">Danger Zone</h1> <p class="text-red-600 dark:text-red-400 mt-1">These actions are permanent and cannot be undone</p></div></div></div></div> <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8"> <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 mb-8"><div class="flex items-start gap-3">${validate_component(Shield, "Shield").$$render(
    $$result,
    {
      class: "h-6 w-6 text-yellow-600 dark:text-yellow-400 shrink-0"
    },
    {},
    {}
  )} <div data-svelte-h="svelte-1oorsuv"><h2 class="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">Important Security Notice</h2> <p class="text-yellow-800 dark:text-yellow-200 mb-3">The actions on this page can significantly impact your account. Please ensure you:</p> <ul class="text-yellow-800 dark:text-yellow-200 space-y-1 list-disc list-inside"><li>Have exported any data you wish to keep</li> <li>Understand that some actions are irreversible</li> <li>Are certain about proceeding with these changes</li></ul></div></div></div>  <div class="space-y-6">${each(dangerousActions, (action) => {
    return `<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden"><div class="p-6"><div class="flex items-start gap-4"><div class="${"p-3 rounded-lg " + escape(
      action.variant === "danger" ? "bg-red-100 dark:bg-red-900/30" : "bg-orange-100 dark:bg-orange-900/30",
      true
    )}">${validate_component(action.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-6 w-6 " + (action.variant === "danger" ? "text-red-600 dark:text-red-400" : "text-orange-600 dark:text-orange-400")
      },
      {},
      {}
    )}</div> <div class="flex-1"><h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${escape(action.title)}</h3> <p class="text-gray-600 dark:text-gray-400 mb-4">${escape(action.description)}</p> <button ${loading ? "disabled" : ""} class="${"px-4 py-2 font-medium rounded-lg transition-colors " + escape(
      action.variant === "danger" ? "bg-red-600 text-white hover:bg-red-700" : "bg-orange-600 text-white hover:bg-orange-700",
      true
    ) + " disabled:opacity-50 disabled:cursor-not-allowed"}">${escape(action.title)} </button></div> </div></div> </div>`;
  })}</div>  <div class="mt-12 text-center text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1jcur0r"><p class="mb-2">Need help? Contact our support team before taking any irreversible actions.</p> <a href="/support" class="text-blue-600 dark:text-blue-400 hover:underline">Contact Support →</a></div></div>  ${showDeactivateModal ? `<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"><div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full"><div class="flex items-center justify-between mb-4"><div class="flex items-center gap-3"><div class="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">${validate_component(Archive, "Archive").$$render(
    $$result,
    {
      class: "h-6 w-6 text-orange-600 dark:text-orange-400"
    },
    {},
    {}
  )}</div> <h2 class="text-xl font-semibold text-gray-900 dark:text-white" data-svelte-h="svelte-1cnn5k4">Archive Account</h2></div> <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">${validate_component(X, "X").$$render($$result, { class: "h-5 w-5" }, {}, {})}</button></div> <div class="space-y-4" data-svelte-h="svelte-bd5r5f"><p class="text-gray-600 dark:text-gray-400">Archiving your account will:</p> <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-2 list-disc list-inside"><li>Temporarily disable access to your account</li> <li>Preserve all your data and settings</li> <li>Allow you to reactivate anytime by logging in</li> <li>Stop any recurring subscriptions</li></ul> <div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg"><p class="text-sm text-blue-800 dark:text-blue-200"><strong>Tip:</strong> This is reversible. You can reactivate your account 
							anytime by logging back in.</p></div></div> <div class="flex gap-3 mt-6"><button class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors" data-svelte-h="svelte-15sqdos">Cancel</button> <button ${loading ? "disabled" : ""} class="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50">${loading ? `${validate_component(LoadingSpinner, "LoadingSpinner").$$render($$result, { size: "sm", color: "white" }, {}, {})}` : `Archive Account`}</button></div></div></div>` : ``}  ${showDeleteModal ? `<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"><div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full"><div class="flex items-center justify-between mb-4"><div class="flex items-center gap-3"><div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">${validate_component(Triangle_alert, "AlertTriangle").$$render(
    $$result,
    {
      class: "h-6 w-6 text-red-600 dark:text-red-400"
    },
    {},
    {}
  )}</div> <h2 class="text-xl font-semibold text-gray-900 dark:text-white" data-svelte-h="svelte-1yxrc87">Delete Account</h2></div> <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">${validate_component(X, "X").$$render($$result, { class: "h-5 w-5" }, {}, {})}</button></div> <div class="space-y-4"><div class="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg" data-svelte-h="svelte-zvtipk"><p class="text-red-800 dark:text-red-200 font-medium mb-2">This action is permanent and cannot be undone!</p> <p class="text-sm text-red-700 dark:text-red-300">All your data, including trades, analytics, and settings will be 
							permanently deleted.</p></div> <p class="text-gray-600 dark:text-gray-400" data-svelte-h="svelte-25p5bq">Deleting your account will:</p> <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-2 list-disc list-inside" data-svelte-h="svelte-1xwli33"><li>Permanently delete all your trading data</li> <li>Remove all analytics and insights</li> <li>Cancel any active subscriptions</li> <li>Delete your profile and settings</li></ul> <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1w9ffyr">Type &quot;DELETE MY ACCOUNT&quot; to confirm:</label> <input type="text" placeholder="DELETE MY ACCOUNT" class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"${add_attribute("value", deleteConfirmation, 0)}></div></div> <div class="flex gap-3 mt-6"><button class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors" data-svelte-h="svelte-105dfbd">Cancel</button> <button ${loading || deleteConfirmation !== "DELETE MY ACCOUNT" ? "disabled" : ""} class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">${loading ? `${validate_component(LoadingSpinner, "LoadingSpinner").$$render($$result, { size: "sm", color: "white" }, {}, {})}` : `Delete Account`}</button></div></div></div>` : ``}</div>`;
});
export {
  Page as default
};
