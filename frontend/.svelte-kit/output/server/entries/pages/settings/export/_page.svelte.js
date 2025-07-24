import { c as create_ssr_component, v as validate_component, e as each, a as add_attribute, b as escape, m as missing_component } from "../../../../chunks/ssr.js";
import { D as Download } from "../../../../chunks/download.js";
import { F as File_spreadsheet } from "../../../../chunks/file-spreadsheet.js";
import { F as File_text } from "../../../../chunks/file-text.js";
import { C as Circle_check_big } from "../../../../chunks/circle-check-big.js";
import { C as Clock } from "../../../../chunks/clock.js";
import { C as Circle_alert } from "../../../../chunks/circle-alert.js";
function formatDate(date) {
  return date.toLocaleDateString() + " " + date.toLocaleTimeString();
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let exportType = "trades";
  let format = "csv";
  let includeOptions = {
    trades: true,
    analytics: true,
    notes: true,
    tags: true,
    performance: true
  };
  let exportHistory = [
    {
      id: "1",
      type: "Full Export",
      format: "CSV",
      date: /* @__PURE__ */ new Date("2024-01-20T10:00:00"),
      size: "2.4 MB",
      status: "completed"
    },
    {
      id: "2",
      type: "Trades Only",
      format: "Excel",
      date: /* @__PURE__ */ new Date("2024-01-15T14:30:00"),
      size: "1.1 MB",
      status: "completed"
    },
    {
      id: "3",
      type: "Tax Report",
      format: "PDF",
      date: /* @__PURE__ */ new Date("2024-01-01T09:00:00"),
      size: "342 KB",
      status: "completed"
    }
  ];
  const exportTypes = [
    {
      value: "trades",
      label: "Trade History",
      icon: File_spreadsheet
    },
    {
      value: "performance",
      label: "Performance Report",
      icon: File_text
    },
    {
      value: "tax",
      label: "Tax Report",
      icon: File_text
    },
    {
      value: "full",
      label: "Full Account Export",
      icon: Download
    }
  ];
  const formats = [
    {
      value: "csv",
      label: "CSV",
      description: "Compatible with Excel, Google Sheets"
    },
    {
      value: "excel",
      label: "Excel",
      description: "Native Excel format with formatting"
    },
    {
      value: "pdf",
      label: "PDF",
      description: "Formatted report for printing"
    },
    {
      value: "json",
      label: "JSON",
      description: "For developers and APIs"
    }
  ];
  const dateRanges = [
    { value: "all", label: "All Time" },
    { value: "ytd", label: "Year to Date" },
    { value: "last_year", label: "Last Year" },
    {
      value: "last_quarter",
      label: "Last Quarter"
    },
    { value: "last_month", label: "Last Month" },
    { value: "custom", label: "Custom Range" }
  ];
  return `${$$result.head += `<!-- HEAD_svelte-1sb7p83_START -->${$$result.title = `<title>Export Data - Settings</title>`, ""}<meta name="description" content="Export your TradeSense trading data in various formats."><!-- HEAD_svelte-1sb7p83_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex items-center gap-3">${validate_component(Download, "Download").$$render(
    $$result,
    {
      class: "h-6 w-6 text-gray-600 dark:text-gray-400"
    },
    {},
    {}
  )} <div data-svelte-h="svelte-1yw3ut2"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">Export Data</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Download your trading data and reports</p></div></div></div></div> <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"><div class="grid grid-cols-1 lg:grid-cols-3 gap-8"> <div class="lg:col-span-2 space-y-6"> <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-m4rt5p">What to Export</h2> <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">${each(exportTypes, (type) => {
    return `<label class="${"flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors " + escape(
      exportType === type.value ? "bg-blue-50 dark:bg-blue-900/30 border-blue-600" : "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600",
      true
    )}"><input type="radio"${add_attribute("value", type.value, 0)} class="sr-only"${type.value === exportType ? add_attribute("checked", true, 1) : ""}> ${validate_component(type.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-5 w-5 text-gray-600 dark:text-gray-400"
      },
      {},
      {}
    )} <span class="font-medium text-gray-900 dark:text-white">${escape(type.label)}</span> </label>`;
  })}</div></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-1toohf7">Export Format</h2> <div class="space-y-3">${each(formats, (fmt) => {
    return `<label class="${"flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors " + escape(
      format === fmt.value ? "bg-blue-50 dark:bg-blue-900/30 border-blue-600" : "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600",
      true
    )}"><input type="radio"${add_attribute("value", fmt.value, 0)} class="mt-1"${fmt.value === format ? add_attribute("checked", true, 1) : ""}> <div><p class="font-medium text-gray-900 dark:text-white">${escape(fmt.label)}</p> <p class="text-sm text-gray-600 dark:text-gray-400">${escape(fmt.description)}</p></div> </label>`;
  })}</div></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-1kznnw7">Date Range</h2> <div class="space-y-4"><select class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white">${each(dateRanges, (range) => {
    return `<option${add_attribute("value", range.value, 0)}>${escape(range.label)}</option>`;
  })}</select> ${``}</div></div>  ${`<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-qnkq7t">Include in Export</h2> <div class="space-y-3">${each(Object.entries(includeOptions), ([option, enabled]) => {
    return `<label class="flex items-center gap-3"><input type="checkbox" class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", includeOptions[option], 1)}> <span class="text-gray-700 dark:text-gray-300 capitalize">${escape(option.replace("_", " "))}</span> </label>`;
  })}</div></div>`}  <button ${""} class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium">${`<div class="flex items-center justify-center gap-2">${validate_component(Download, "Download").$$render($$result, { class: "h-5 w-5" }, {}, {})}
							Start Export</div>`}</button></div>  <div class="lg:col-span-1"><div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-nbiwpi">Recent Exports</h2> ${exportHistory.length === 0 ? `<p class="text-gray-600 dark:text-gray-400 text-center py-8" data-svelte-h="svelte-3tmq3b">No exports yet</p>` : `<div class="space-y-3">${each(exportHistory, (item) => {
    return `<div class="p-3 border border-gray-200 dark:border-gray-700 rounded-lg"><div class="flex items-start justify-between mb-2"><div><p class="font-medium text-gray-900 dark:text-white">${escape(item.type)}</p> <p class="text-xs text-gray-500 dark:text-gray-400">${escape(item.format)} • ${escape(item.size)} </p></div> ${item.status === "completed" ? `${validate_component(Circle_check_big, "CheckCircle").$$render(
      $$result,
      {
        class: "h-4 w-4 text-green-600 dark:text-green-400"
      },
      {},
      {}
    )}` : `${validate_component(Clock, "Clock").$$render(
      $$result,
      {
        class: "h-4 w-4 text-yellow-600 dark:text-yellow-400"
      },
      {},
      {}
    )}`}</div> <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">${escape(formatDate(item.date))}</p> <button class="text-sm text-blue-600 dark:text-blue-400 hover:underline" data-svelte-h="svelte-1n1f5xd">Download Again</button> </div>`;
  })}</div>`}</div>  <div class="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4"><div class="flex items-start gap-3">${validate_component(Circle_alert, "AlertCircle").$$render(
    $$result,
    {
      class: "h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0"
    },
    {},
    {}
  )} <div class="text-sm" data-svelte-h="svelte-137kdjf"><p class="font-medium text-blue-900 dark:text-blue-200 mb-1">Export Tips</p> <ul class="text-blue-800 dark:text-blue-300 space-y-1"><li>• CSV format works with most spreadsheet apps</li> <li>• PDF exports include charts and formatting</li> <li>• Tax reports follow IRS Form 8949 format</li> <li>• Large exports may take a few minutes</li></ul></div></div></div></div></div></div></div>`;
});
export {
  Page as default
};
