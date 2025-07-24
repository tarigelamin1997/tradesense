import { c as create_ssr_component, a as add_attribute, v as validate_component, e as each, b as escape, m as missing_component } from "../../../chunks/ssr.js";
import { S as Search } from "../../../chunks/search.js";
import { R as Rocket } from "../../../chunks/rocket.js";
import { U as Upload } from "../../../chunks/upload.js";
import { C as Chart_column } from "../../../chunks/chart-column.js";
import { S as Settings } from "../../../chunks/settings.js";
import { C as Chevron_right } from "../../../chunks/chevron-right.js";
import { V as Video, C as Code } from "../../../chunks/video.js";
import { F as File_text } from "../../../chunks/file-text.js";
import { B as Book_open } from "../../../chunks/book-open.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let filteredCategories;
  let searchQuery = "";
  const quickStart = [
    {
      icon: Rocket,
      title: "Getting Started",
      description: "Learn the basics of TradeSense and set up your account",
      link: "/docs/getting-started"
    },
    {
      icon: Upload,
      title: "Import Your Trades",
      description: "Import trades from your broker or trading platform",
      link: "/docs/importing-trades"
    },
    {
      icon: Chart_column,
      title: "Analyze Performance",
      description: "Understand your trading metrics and analytics",
      link: "/docs/analytics"
    },
    {
      icon: Settings,
      title: "Customize Settings",
      description: "Configure TradeSense to match your trading style",
      link: "/docs/settings"
    }
  ];
  const categories = [
    {
      title: "Platform Basics",
      icon: Book_open,
      articles: [
        {
          title: "Account Setup",
          link: "/docs/account-setup"
        },
        {
          title: "Dashboard Overview",
          link: "/docs/dashboard"
        },
        {
          title: "Navigation Guide",
          link: "/docs/navigation"
        },
        {
          title: "Keyboard Shortcuts",
          link: "/docs/shortcuts"
        }
      ]
    },
    {
      title: "Trade Management",
      icon: File_text,
      articles: [
        {
          title: "Adding Trades Manually",
          link: "/docs/manual-trades"
        },
        {
          title: "Bulk Import",
          link: "/docs/bulk-import"
        },
        {
          title: "Trade Types & Categories",
          link: "/docs/trade-types"
        },
        {
          title: "Tags & Organization",
          link: "/docs/tags"
        }
      ]
    },
    {
      title: "Analytics & Reports",
      icon: Chart_column,
      articles: [
        {
          title: "Performance Metrics",
          link: "/docs/metrics"
        },
        {
          title: "Custom Reports",
          link: "/docs/custom-reports"
        },
        {
          title: "Exporting Data",
          link: "/docs/export"
        },
        {
          title: "AI Insights",
          link: "/docs/ai-insights"
        }
      ]
    },
    {
      title: "API & Integrations",
      icon: Code,
      articles: [
        { title: "API Overview", link: "/docs/api" },
        {
          title: "Authentication",
          link: "/docs/api-auth"
        },
        {
          title: "Webhooks",
          link: "/docs/webhooks"
        },
        {
          title: "Broker Integrations",
          link: "/docs/integrations"
        }
      ]
    }
  ];
  const resources = [
    {
      icon: Video,
      title: "Video Tutorials",
      description: "Step-by-step video guides",
      link: "/docs/videos"
    },
    {
      icon: Code,
      title: "API Reference",
      description: "Complete API documentation",
      link: "/docs/api-reference"
    },
    {
      icon: File_text,
      title: "Release Notes",
      description: "Latest updates and changes",
      link: "/changelog"
    }
  ];
  filteredCategories = categories;
  return `${$$result.head += `<!-- HEAD_svelte-187qskt_START -->${$$result.title = `<title>Documentation - TradeSense</title>`, ""}<meta name="description" content="Complete documentation for TradeSense trading analytics platform. Learn how to import trades, analyze performance, and use our API."><!-- HEAD_svelte-187qskt_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-gray-50 dark:from-gray-800 dark:to-gray-900"><div class="max-w-7xl mx-auto text-center"><h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6" data-svelte-h="svelte-1oayrgt">Documentation</h1> <p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-8" data-svelte-h="svelte-9scyrd">Everything you need to know about using TradeSense to track, analyze, and improve your trading performance.</p>  <div class="max-w-xl mx-auto"><div class="relative"><input type="text" placeholder="Search documentation..." class="w-full px-4 py-3 pl-12 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"${add_attribute("value", searchQuery, 0)}> ${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400"
    },
    {},
    {}
  )}</div></div></div></section>  <section class="py-16 px-4 sm:px-6 lg:px-8"><div class="max-w-7xl mx-auto"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8" data-svelte-h="svelte-1adzbir">Quick Start Guides</h2> <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">${each(quickStart, (guide) => {
    return `<a${add_attribute("href", guide.link, 0)} class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700"><div class="flex items-start gap-4"><div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg shrink-0">${validate_component(guide.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-6 w-6 text-blue-600 dark:text-blue-400"
      },
      {},
      {}
    )}</div> <div><h3 class="font-semibold text-gray-900 dark:text-white mb-1">${escape(guide.title)}</h3> <p class="text-sm text-gray-600 dark:text-gray-400">${escape(guide.description)}</p> </div></div> </a>`;
  })}</div></div></section>  <section class="py-16 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800"><div class="max-w-7xl mx-auto"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8" data-svelte-h="svelte-nh7y2k">Browse by Category</h2> <div class="grid lg:grid-cols-2 gap-8">${each(filteredCategories, (category) => {
    return `<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-6"><div class="flex items-center gap-3 mb-4"><div class="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm">${validate_component(category.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-6 w-6 text-gray-700 dark:text-gray-300"
      },
      {},
      {}
    )}</div> <h3 class="text-lg font-semibold text-gray-900 dark:text-white">${escape(category.title)} </h3></div> <ul class="space-y-2">${each(category.articles, (article) => {
      return `<li><a${add_attribute("href", article.link, 0)} class="flex items-center justify-between p-2 rounded hover:bg-white dark:hover:bg-gray-800 transition-colors group"><span class="text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">${escape(article.title)}</span> ${validate_component(Chevron_right, "ChevronRight").$$render(
        $$result,
        {
          class: "h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400"
        },
        {},
        {}
      )}</a> </li>`;
    })}</ul> </div>`;
  })}</div> ${``}</div></section>  <section class="py-16 px-4 sm:px-6 lg:px-8"><div class="max-w-7xl mx-auto"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8" data-svelte-h="svelte-1ejpqcz">Additional Resources</h2> <div class="grid md:grid-cols-3 gap-6">${each(resources, (resource) => {
    return `<a${add_attribute("href", resource.link, 0)} class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700"><div class="flex items-start gap-4"><div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg shrink-0">${validate_component(resource.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-6 w-6 text-gray-700 dark:text-gray-300"
      },
      {},
      {}
    )}</div> <div><h3 class="font-semibold text-gray-900 dark:text-white mb-1">${escape(resource.title)}</h3> <p class="text-sm text-gray-600 dark:text-gray-400">${escape(resource.description)}</p> </div></div> </a>`;
  })}</div></div></section>  <section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20" data-svelte-h="svelte-bcheeg"><div class="max-w-4xl mx-auto text-center"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Can&#39;t find what you&#39;re looking for?</h2> <p class="text-gray-600 dark:text-gray-400 mb-6">Our support team is here to help you get the most out of TradeSense.</p> <div class="flex flex-wrap justify-center gap-4"><a href="/contact" class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">Contact Support</a> <a href="/support/kb" class="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium border border-gray-300 dark:border-gray-600">Browse FAQs</a></div></div></section></div>`;
});
export {
  Page as default
};
