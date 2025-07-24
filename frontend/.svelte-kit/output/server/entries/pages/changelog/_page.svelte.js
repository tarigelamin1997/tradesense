import { c as create_ssr_component, v as validate_component, b as escape, e as each, m as missing_component } from "../../../chunks/ssr.js";
import { P as Package, G as Git_commit_horizontal, B as Bug } from "../../../chunks/package.js";
import { C as Check } from "../../../chunks/check.js";
import { C as Circle_alert } from "../../../chunks/circle-alert.js";
import { S as Shield } from "../../../chunks/shield.js";
import { Z as Zap } from "../../../chunks/zap.js";
import { S as Sparkles } from "../../../chunks/sparkles.js";
function getCategoryColor(category) {
  switch (category) {
    case "features":
      return "text-blue-600 dark:text-blue-400";
    case "improvements":
      return "text-green-600 dark:text-green-400";
    case "fixes":
      return "text-orange-600 dark:text-orange-400";
    case "security":
      return "text-red-600 dark:text-red-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
}
function getVersionBadgeColor(type) {
  switch (type) {
    case "major":
      return "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400";
    case "minor":
      return "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400";
    case "patch":
      return "bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400";
    default:
      return "bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400";
  }
}
function formatDate(date) {
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric"
  });
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let changelog = [
    {
      version: "2.5.0",
      date: /* @__PURE__ */ new Date("2024-01-22"),
      type: "minor",
      changes: [
        {
          category: "features",
          items: [
            "Added AI-powered trade insights and recommendations",
            "New portfolio rebalancing tool with automated suggestions",
            "Multi-currency support for international traders"
          ]
        },
        {
          category: "improvements",
          items: [
            "Enhanced dashboard performance with 50% faster load times",
            "Improved mobile responsiveness across all pages",
            "Better error handling and user feedback"
          ]
        },
        {
          category: "fixes",
          items: [
            "Fixed CSV import issues with special characters",
            "Resolved timezone conversion bugs in trade history"
          ]
        }
      ]
    },
    {
      version: "2.4.2",
      date: /* @__PURE__ */ new Date("2024-01-10"),
      type: "patch",
      changes: [
        {
          category: "security",
          items: [
            "Updated authentication system with enhanced security",
            "Implemented rate limiting on API endpoints"
          ]
        },
        {
          category: "fixes",
          items: [
            "Fixed calculation errors in P&L reports",
            "Resolved dark mode styling issues",
            "Corrected date filtering in analytics"
          ]
        }
      ]
    },
    {
      version: "2.4.0",
      date: /* @__PURE__ */ new Date("2023-12-15"),
      type: "minor",
      changes: [
        {
          category: "features",
          items: [
            "Interactive Brokers direct integration",
            "Real-time trade synchronization",
            "Custom alert system with email/SMS notifications"
          ]
        },
        {
          category: "improvements",
          items: [
            "Redesigned analytics dashboard",
            "Added more chart types and indicators",
            "Improved trade tagging system"
          ]
        }
      ]
    },
    {
      version: "2.3.0",
      date: /* @__PURE__ */ new Date("2023-11-20"),
      type: "minor",
      changes: [
        {
          category: "features",
          items: [
            "Tax report generation for multiple jurisdictions",
            "Batch trade import from CSV/Excel",
            "Performance comparison with market indices"
          ]
        },
        {
          category: "improvements",
          items: [
            "Faster search functionality",
            "Better mobile app performance",
            "Enhanced data export options"
          ]
        },
        {
          category: "fixes",
          items: ["Fixed rounding errors in calculations", "Resolved API timeout issues"]
        }
      ]
    }
  ];
  function getCategoryIcon(category) {
    switch (category) {
      case "features":
        return Sparkles;
      case "improvements":
        return Zap;
      case "fixes":
        return Bug;
      case "security":
        return Shield;
      default:
        return Git_commit_horizontal;
    }
  }
  return `${$$result.head += `<!-- HEAD_svelte-183p50u_START -->${$$result.title = `<title>Changelog - TradeSense Updates</title>`, ""}<meta name="description" content="Stay up to date with the latest features, improvements, and fixes in TradeSense."><!-- HEAD_svelte-183p50u_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12"><div class="text-center"><div class="inline-flex p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">${validate_component(Package, "Package").$$render(
    $$result,
    {
      class: "h-8 w-8 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )}</div> <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-wddpl">Changelog</h1> <p class="text-xl text-gray-600 dark:text-gray-400" data-svelte-h="svelte-yl5zoz">Track all updates and improvements to TradeSense</p></div></div></div>  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 flex items-center gap-3">${validate_component(Check, "Check").$$render(
    $$result,
    {
      class: "h-5 w-5 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )} <p class="text-blue-800 dark:text-blue-200">You&#39;re currently on version <strong>${escape(changelog[0].version)}</strong> - the latest release!</p></div></div>  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-12"><div class="space-y-8">${each(changelog, (entry) => {
    return `<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden"> <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700"><div class="flex items-center justify-between"><div class="flex items-center gap-3"><h2 class="text-2xl font-bold text-gray-900 dark:text-white">v${escape(entry.version)}</h2> <span class="${"px-2 py-1 text-xs font-medium rounded-full " + escape(getVersionBadgeColor(entry.type), true)}">${escape(entry.type.toUpperCase())} </span></div> <time class="text-gray-500 dark:text-gray-400">${escape(formatDate(entry.date))}</time> </div></div>  <div class="p-6 space-y-6">${each(entry.changes, (changeGroup) => {
      return `<div><div class="flex items-center gap-2 mb-3">${validate_component(getCategoryIcon(changeGroup.category) || missing_component, "svelte:component").$$render(
        $$result,
        {
          class: "h-5 w-5 " + getCategoryColor(changeGroup.category)
        },
        {},
        {}
      )} <h3 class="font-semibold text-gray-900 dark:text-white capitalize">${escape(changeGroup.category)} </h3></div> <ul class="space-y-2 ml-7">${each(changeGroup.items, (item) => {
        return `<li class="text-gray-600 dark:text-gray-400 flex items-start gap-2"><span class="text-gray-400 dark:text-gray-600 mt-1.5" data-svelte-h="svelte-1iio1xx">•</span> <span>${escape(item)}</span> </li>`;
      })}</ul> </div>`;
    })}</div> </div>`;
  })}</div>  <div class="mt-12 text-center" data-svelte-h="svelte-jt5w5l"><p class="text-gray-500 dark:text-gray-400 mb-4">That&#39;s all for now! Check back regularly for updates.</p> <div class="flex flex-wrap justify-center gap-4 text-sm"><a href="/roadmap" class="text-blue-600 dark:text-blue-400 hover:underline">View Roadmap →</a> <a href="/docs/api/webhooks" class="text-blue-600 dark:text-blue-400 hover:underline">Subscribe to Updates →</a> <a href="https://github.com/tradesense/releases" class="text-blue-600 dark:text-blue-400 hover:underline">GitHub Releases →</a></div></div></div>  <section class="bg-gray-100 dark:bg-gray-800 py-12"><div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center"><div class="inline-flex p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg mb-4">${validate_component(Circle_alert, "AlertCircle").$$render(
    $$result,
    {
      class: "h-6 w-6 text-yellow-600 dark:text-yellow-400"
    },
    {},
    {}
  )}</div> <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-3" data-svelte-h="svelte-mkgaq0">Never Miss an Update</h2> <p class="text-gray-600 dark:text-gray-400 mb-6" data-svelte-h="svelte-u32d87">Get notified about new features and important updates</p> <form class="flex flex-col sm:flex-row gap-3 max-w-md mx-auto" data-svelte-h="svelte-14slvnu"><input type="email" placeholder="your@email.com" class="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"> <button type="submit" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">Subscribe</button></form></div></section></div>`;
});
export {
  Page as default
};
