import { c as create_ssr_component, v as validate_component, e as each, a as add_attribute, b as escape, m as missing_component } from "../../../chunks/ssr.js";
import { M as Map, C as Circle } from "../../../chunks/map.js";
import { C as Circle_check_big } from "../../../chunks/circle-check-big.js";
import { C as Clock } from "../../../chunks/clock.js";
import { T as Target } from "../../../chunks/target.js";
import { T as Thumbs_up } from "../../../chunks/thumbs-up.js";
import { R as Rocket } from "../../../chunks/rocket.js";
import { U as Users } from "../../../chunks/users.js";
function getStatusColor(status) {
  switch (status) {
    case "completed":
      return "text-green-600 dark:text-green-400";
    case "in-progress":
      return "text-blue-600 dark:text-blue-400";
    case "planned":
      return "text-gray-400 dark:text-gray-600";
    default:
      return "text-gray-400 dark:text-gray-600";
  }
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let quarters;
  let categories;
  let filteredItems;
  let groupedItems;
  let roadmapItems = [
    // Q1 2024
    {
      id: "1",
      title: "AI-Powered Trade Analysis",
      description: "Machine learning algorithms to analyze your trading patterns and provide personalized insights.",
      status: "completed",
      quarter: "Q1 2024",
      category: "AI & Analytics",
      votes: 234
    },
    {
      id: "2",
      title: "Multi-Currency Support",
      description: "Track and analyze trades across multiple currencies with automatic conversion.",
      status: "completed",
      quarter: "Q1 2024",
      category: "Core Features",
      votes: 189
    },
    {
      id: "3",
      title: "Mobile App Launch",
      description: "Native iOS and Android apps for tracking trades on the go.",
      status: "in-progress",
      quarter: "Q1 2024",
      category: "Platform",
      votes: 412,
      progress: 75
    },
    // Q2 2024
    {
      id: "4",
      title: "Options Trading Support",
      description: "Full support for options trading including Greeks calculation and strategy analysis.",
      status: "in-progress",
      quarter: "Q2 2024",
      category: "Trading Features",
      votes: 356,
      progress: 40
    },
    {
      id: "5",
      title: "Advanced Backtesting",
      description: "Test your trading strategies against historical data with detailed performance metrics.",
      status: "planned",
      quarter: "Q2 2024",
      category: "Analytics",
      votes: 278
    },
    {
      id: "6",
      title: "Social Trading Features",
      description: "Follow top traders, share strategies, and learn from the community.",
      status: "planned",
      quarter: "Q2 2024",
      category: "Community",
      votes: 167
    },
    // Q3 2024
    {
      id: "7",
      title: "Automated Trading Rules",
      description: "Set up automated alerts and actions based on custom trading rules.",
      status: "planned",
      quarter: "Q3 2024",
      category: "Automation",
      votes: 445
    },
    {
      id: "8",
      title: "Advanced Risk Management",
      description: "Sophisticated risk analysis tools including VaR, stress testing, and portfolio optimization.",
      status: "planned",
      quarter: "Q3 2024",
      category: "Risk Management",
      votes: 323
    },
    // Q4 2024
    {
      id: "9",
      title: "Crypto Trading Integration",
      description: "Connect cryptocurrency exchanges and track crypto trades alongside traditional assets.",
      status: "planned",
      quarter: "Q4 2024",
      category: "Integrations",
      votes: 567
    },
    {
      id: "10",
      title: "Team Collaboration",
      description: "Tools for trading teams to collaborate, share insights, and manage permissions.",
      status: "planned",
      quarter: "Q4 2024",
      category: "Enterprise",
      votes: 145
    }
  ];
  let selectedCategory = "all";
  function getStatusIcon(status) {
    switch (status) {
      case "completed":
        return Circle_check_big;
      case "in-progress":
        return Clock;
      case "planned":
        return Circle;
      default:
        return Circle;
    }
  }
  quarters = ["all", ...new Set(roadmapItems.map((item) => item.quarter))];
  categories = ["all", ...new Set(roadmapItems.map((item) => item.category))];
  filteredItems = roadmapItems.filter((item) => {
    const matchesCategory = selectedCategory === "all";
    return matchesCategory;
  });
  groupedItems = filteredItems.reduce(
    (acc, item) => {
      if (!acc[item.quarter]) {
        acc[item.quarter] = [];
      }
      acc[item.quarter].push(item);
      return acc;
    },
    {}
  );
  return `${$$result.head += `<!-- HEAD_svelte-1lz2zc8_START -->${$$result.title = `<title>Roadmap - TradeSense Future</title>`, ""}<meta name="description" content="See what's coming next to TradeSense. Vote on features and track our progress."><!-- HEAD_svelte-1lz2zc8_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"><div class="text-center"><div class="inline-flex p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full mb-4">${validate_component(Map, "Map").$$render(
    $$result,
    {
      class: "h-8 w-8 text-purple-600 dark:text-purple-400"
    },
    {},
    {}
  )}</div> <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-q2fkta">Product Roadmap</h1> <p class="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto" data-svelte-h="svelte-1ko607i">See what we&#39;re building next and help shape the future of TradeSense</p></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex flex-col sm:flex-row gap-4"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1di40zs">Quarter</label> <select class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white">${each(quarters, (quarter) => {
    return `<option${add_attribute("value", quarter, 0)}>${escape(quarter === "all" ? "All Quarters" : quarter)} </option>`;
  })}</select></div> <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-4f69k8">Category</label> <select class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white">${each(categories, (category) => {
    return `<option${add_attribute("value", category, 0)}>${escape(category === "all" ? "All Categories" : category)} </option>`;
  })}</select></div></div>  <div class="flex flex-wrap gap-6 mt-6"><div class="flex items-center gap-2">${validate_component(Circle_check_big, "CheckCircle").$$render(
    $$result,
    {
      class: "h-5 w-5 text-green-600 dark:text-green-400"
    },
    {},
    {}
  )} <span class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-89rr6q">Completed</span></div> <div class="flex items-center gap-2">${validate_component(Clock, "Clock").$$render(
    $$result,
    {
      class: "h-5 w-5 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )} <span class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-zezwdd">In Progress</span></div> <div class="flex items-center gap-2">${validate_component(Circle, "Circle").$$render(
    $$result,
    {
      class: "h-5 w-5 text-gray-400 dark:text-gray-600"
    },
    {},
    {}
  )} <span class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1xpmgt5">Planned</span></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">${each(Object.entries(groupedItems), ([quarter, items]) => {
    return `<div class="mb-8"><h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">${validate_component(Target, "Target").$$render($$result, { class: "h-5 w-5" }, {}, {})} ${escape(quarter)}</h2> <div class="grid grid-cols-1 md:grid-cols-2 gap-4">${each(items, (item) => {
      return `<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><div class="flex items-start justify-between mb-3"><div class="flex items-center gap-3">${validate_component(getStatusIcon(item.status) || missing_component, "svelte:component").$$render(
        $$result,
        {
          class: "h-5 w-5 " + getStatusColor(item.status)
        },
        {},
        {}
      )} <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">${escape(item.category)} </span></div> <button class="flex items-center gap-1 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">${validate_component(Thumbs_up, "ThumbsUp").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span class="text-sm">${escape(item.votes)}</span> </button></div> <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${escape(item.title)}</h3> <p class="text-gray-600 dark:text-gray-400 mb-4">${escape(item.description)}</p> ${item.status === "in-progress" && item.progress ? `<div class="mb-3"><div class="flex items-center justify-between text-sm mb-1"><span class="text-gray-600 dark:text-gray-400" data-svelte-h="svelte-2d9ick">Progress</span> <span class="text-gray-900 dark:text-white font-medium">${escape(item.progress)}%</span></div> <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2"><div class="bg-blue-600 h-2 rounded-full transition-all" style="${"width: " + escape(item.progress, true) + "%"}"></div></div> </div>` : ``} <div class="flex items-center gap-4 text-sm"><span class="${"flex items-center gap-1 " + escape(getStatusColor(item.status), true)}">${validate_component(getStatusIcon(item.status) || missing_component, "svelte:component").$$render($$result, { class: "h-4 w-4" }, {}, {})} ${escape(item.status.replace("-", " "))} </span></div> </div>`;
    })}</div> </div>`;
  })}</div>  <section class="bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-800 dark:to-purple-800"><div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center"><div class="inline-flex p-3 bg-white/20 rounded-full mb-4">${validate_component(Rocket, "Rocket").$$render($$result, { class: "h-8 w-8 text-white" }, {}, {})}</div> <h2 class="text-3xl font-bold text-white mb-4" data-svelte-h="svelte-8058jm">Have a Feature Request?</h2> <p class="text-blue-100 mb-8 text-lg" data-svelte-h="svelte-1caqmy2">We&#39;d love to hear your ideas! Help us build the trading platform you need.</p> <div class="flex flex-wrap justify-center gap-4" data-svelte-h="svelte-1fy8v3t"><a href="/support/feature-request" class="px-6 py-3 bg-white text-blue-600 rounded-lg font-medium hover:bg-gray-100 transition-colors">Submit Feature Request</a> <a href="/community" class="px-6 py-3 bg-transparent text-white border-2 border-white rounded-lg font-medium hover:bg-white/10 transition-colors">Join Community Discussion</a></div></div></section>  <section class="py-12"><div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center"><div class="inline-flex p-3 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">${validate_component(Users, "Users").$$render(
    $$result,
    {
      class: "h-8 w-8 text-green-600 dark:text-green-400"
    },
    {},
    {}
  )}</div> <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-192hvop">Built with Your Feedback</h2> <p class="text-gray-600 dark:text-gray-400 mb-8" data-svelte-h="svelte-un5bge">Over 2,000 traders have contributed ideas and feedback to shape TradeSense</p> <div class="grid grid-cols-1 md:grid-cols-3 gap-6" data-svelte-h="svelte-fztrrl"><div class="text-center"><p class="text-3xl font-bold text-gray-900 dark:text-white mb-2">5,234</p> <p class="text-gray-600 dark:text-gray-400">Feature Votes</p></div> <div class="text-center"><p class="text-3xl font-bold text-gray-900 dark:text-white mb-2">342</p> <p class="text-gray-600 dark:text-gray-400">Ideas Submitted</p></div> <div class="text-center"><p class="text-3xl font-bold text-gray-900 dark:text-white mb-2">89</p> <p class="text-gray-600 dark:text-gray-400">Features Shipped</p></div></div></div></section></div>`;
});
export {
  Page as default
};
