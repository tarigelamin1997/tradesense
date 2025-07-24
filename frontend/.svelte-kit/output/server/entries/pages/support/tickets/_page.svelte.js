import { c as create_ssr_component, v as validate_component, a as add_attribute, e as each, b as escape, m as missing_component } from "../../../../chunks/ssr.js";
import "@sveltejs/kit/internal";
import "../../../../chunks/exports.js";
import "../../../../chunks/state.svelte.js";
import { P as Plus } from "../../../../chunks/plus.js";
import { S as Search } from "../../../../chunks/search.js";
import { F as Funnel } from "../../../../chunks/funnel.js";
import { M as Message_square } from "../../../../chunks/message-square.js";
import { C as Chevron_right } from "../../../../chunks/chevron-right.js";
import { C as Clock } from "../../../../chunks/clock.js";
import { C as Circle_check_big } from "../../../../chunks/circle-check-big.js";
import { C as Circle_alert } from "../../../../chunks/circle-alert.js";
function getStatusColor(status) {
  switch (status) {
    case "open":
      return "text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30";
    case "in_progress":
      return "text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30";
    case "resolved":
      return "text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30";
    case "closed":
      return "text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30";
    default:
      return "text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30";
  }
}
function getPriorityColor(priority) {
  switch (priority) {
    case "urgent":
      return "text-red-600 dark:text-red-400";
    case "high":
      return "text-orange-600 dark:text-orange-400";
    case "medium":
      return "text-yellow-600 dark:text-yellow-400";
    case "low":
      return "text-gray-600 dark:text-gray-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
}
function formatDate(date) {
  const now = /* @__PURE__ */ new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1e3 * 60 * 60 * 24));
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return date.toLocaleDateString();
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let filteredTickets;
  let tickets = [
    {
      id: "1",
      subject: "Unable to import trades from Interactive Brokers",
      status: "in_progress",
      priority: "high",
      createdAt: /* @__PURE__ */ new Date("2024-01-20"),
      updatedAt: /* @__PURE__ */ new Date("2024-01-21"),
      lastMessage: "We're looking into this issue and will update you soon.",
      unreadCount: 1
    },
    {
      id: "2",
      subject: "Question about subscription billing",
      status: "resolved",
      priority: "medium",
      createdAt: /* @__PURE__ */ new Date("2024-01-18"),
      updatedAt: /* @__PURE__ */ new Date("2024-01-19"),
      lastMessage: "Your subscription has been updated successfully.",
      unreadCount: 0
    }
  ];
  let searchQuery = "";
  let filterStatus = "all";
  function getStatusIcon(status) {
    switch (status) {
      case "open":
      case "in_progress":
        return Circle_alert;
      case "resolved":
      case "closed":
        return Circle_check_big;
      default:
        return Clock;
    }
  }
  filteredTickets = tickets.filter((ticket) => {
    const matchesStatus = filterStatus === "all";
    return matchesStatus;
  });
  return `${$$result.head += `<!-- HEAD_svelte-1nwmo46_START -->${$$result.title = `<title>Support Tickets - TradeSense</title>`, ""}<meta name="description" content="View and manage your support tickets with TradeSense."><!-- HEAD_svelte-1nwmo46_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex items-center justify-between"><div data-svelte-h="svelte-10x27fn"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">Support Tickets</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Track and manage your support requests</p></div> <button class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">${validate_component(Plus, "Plus").$$render($$result, { class: "h-5 w-5" }, {}, {})}
					New Ticket</button></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex flex-col sm:flex-row gap-4"> <div class="flex-1 relative"><input type="text" placeholder="Search tickets..." class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"${add_attribute("value", searchQuery, 0)}> ${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400"
    },
    {},
    {}
  )}</div>  <div class="flex items-center gap-2">${validate_component(Funnel, "Filter").$$render($$result, { class: "h-5 w-5 text-gray-400" }, {}, {})} <select class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"><option value="all" data-svelte-h="svelte-rskcdc">All Status</option><option value="open" data-svelte-h="svelte-14z723y">Open</option><option value="in_progress" data-svelte-h="svelte-7y42mr">In Progress</option><option value="resolved" data-svelte-h="svelte-1tursri">Resolved</option><option value="closed" data-svelte-h="svelte-106rur2">Closed</option></select></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">${`${filteredTickets.length === 0 ? `<div class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">${validate_component(Message_square, "MessageSquare").$$render(
    $$result,
    {
      class: "h-12 w-12 text-gray-400 mx-auto mb-4"
    },
    {},
    {}
  )} <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2" data-svelte-h="svelte-rj4uoq">No tickets found</h3> <p class="text-gray-600 dark:text-gray-400 mb-6">${`${`You haven&#39;t created any support tickets yet.`}`}</p> ${filteredTickets.length === 0 && !searchQuery && filterStatus === "all" ? `<button class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">${validate_component(Plus, "Plus").$$render($$result, { class: "h-5 w-5" }, {}, {})}
						Create Your First Ticket</button>` : ``}</div>` : `<div class="space-y-4">${each(filteredTickets, (ticket) => {
    return `<a href="${"/support/tickets/" + escape(ticket.id, true)}" class="block bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow p-6"><div class="flex items-start justify-between"><div class="flex-1"><div class="flex items-start gap-4"><div class="${"p-2 rounded-lg " + escape(getStatusColor(ticket.status), true)}">${validate_component(getStatusIcon(ticket.status) || missing_component, "svelte:component").$$render($$result, { class: "h-5 w-5" }, {}, {})}</div> <div class="flex-1"><div class="flex items-center gap-3 mb-2"><h3 class="text-lg font-semibold text-gray-900 dark:text-white">${escape(ticket.subject)}</h3> ${ticket.unreadCount > 0 ? `<span class="px-2 py-1 bg-blue-600 text-white text-xs rounded-full">${escape(ticket.unreadCount)} new
												</span>` : ``}</div> <p class="text-gray-600 dark:text-gray-400 mb-3">${escape(ticket.lastMessage)}</p> <div class="flex items-center gap-4 text-sm"><span class="${"capitalize px-2 py-1 rounded " + escape(getStatusColor(ticket.status), true)}">${escape(ticket.status.replace("_", " "))}</span> <span class="${"capitalize " + escape(getPriorityColor(ticket.priority), true)}">${escape(ticket.priority)} priority</span> <span class="text-gray-500 dark:text-gray-400">Updated ${escape(formatDate(ticket.updatedAt))}</span> </div></div> </div></div> ${validate_component(Chevron_right, "ChevronRight").$$render($$result, { class: "h-5 w-5 text-gray-400 shrink-0" }, {}, {})}</div> </a>`;
  })}</div>`}`}</div>  <section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20" data-svelte-h="svelte-s150ze"><div class="max-w-4xl mx-auto text-center"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">Need immediate assistance?</h2> <p class="text-gray-600 dark:text-gray-400 mb-6">Check our knowledge base for instant answers or start a live chat.</p> <div class="flex flex-wrap justify-center gap-4"><a href="/support/kb" class="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium border border-gray-300 dark:border-gray-600">Browse Knowledge Base</a> <button class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">Start Live Chat</button></div></div></section></div>`;
});
export {
  Page as default
};
