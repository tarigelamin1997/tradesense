import { c as create_ssr_component, b as escape, v as validate_component, a as add_attribute, e as each, m as missing_component } from "../../../../chunks/ssr.js";
import { C as Circle_alert } from "../../../../chunks/circle-alert.js";
import { C as Clock } from "../../../../chunks/clock.js";
import { C as Circle_check_big } from "../../../../chunks/circle-check-big.js";
import { M as Message_square } from "../../../../chunks/message-square.js";
import { S as Search } from "../../../../chunks/search.js";
import { U as User } from "../../../../chunks/user.js";
import { C as Circle_x } from "../../../../chunks/circle-x.js";
function getStatusColor(status) {
  switch (status) {
    case "open":
      return "text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30";
    case "in_progress":
      return "text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30";
    case "resolved":
      return "text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30";
    case "closed":
      return "text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30";
    default:
      return "text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30";
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
      return "text-green-600 dark:text-green-400";
    default:
      return "text-gray-600 dark:text-gray-400";
  }
}
function formatTime(date) {
  const now = /* @__PURE__ */ new Date();
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / (1e3 * 60 * 60));
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let filteredTickets;
  let stats;
  let tickets = [
    {
      id: "TICK-1234",
      user: {
        name: "John Doe",
        email: "john@example.com",
        tier: "Professional"
      },
      subject: "Unable to export trades to CSV",
      status: "open",
      priority: "high",
      category: "Technical",
      createdAt: /* @__PURE__ */ new Date("2024-01-22T10:00:00"),
      updatedAt: /* @__PURE__ */ new Date("2024-01-22T10:00:00"),
      messages: 1
    },
    {
      id: "TICK-1233",
      user: {
        name: "Jane Smith",
        email: "jane@example.com",
        tier: "Starter"
      },
      subject: "Question about subscription upgrade",
      status: "in_progress",
      priority: "medium",
      category: "Billing",
      createdAt: /* @__PURE__ */ new Date("2024-01-21T14:30:00"),
      updatedAt: /* @__PURE__ */ new Date("2024-01-22T09:15:00"),
      assignedTo: "Support Agent 1",
      messages: 3
    },
    {
      id: "TICK-1232",
      user: {
        name: "Bob Johnson",
        email: "bob@example.com",
        tier: "Enterprise"
      },
      subject: "API rate limit increase request",
      status: "resolved",
      priority: "urgent",
      category: "API",
      createdAt: /* @__PURE__ */ new Date("2024-01-20T08:00:00"),
      updatedAt: /* @__PURE__ */ new Date("2024-01-21T16:45:00"),
      assignedTo: "Support Agent 2",
      messages: 5
    }
  ];
  let searchQuery = "";
  let filterPriority = "all";
  function getStatusIcon(status) {
    switch (status) {
      case "open":
        return Circle_alert;
      case "in_progress":
        return Clock;
      case "resolved":
        return Circle_check_big;
      case "closed":
        return Circle_x;
      default:
        return Message_square;
    }
  }
  filteredTickets = tickets.filter((ticket) => {
    const matchesPriority = filterPriority === "all";
    return matchesPriority;
  });
  stats = {
    open: tickets.filter((t) => t.status === "open").length,
    inProgress: tickets.filter((t) => t.status === "in_progress").length,
    resolved: tickets.filter((t) => t.status === "resolved").length,
    avgResponseTime: "2.5 hours"
  };
  return `${$$result.head += `<!-- HEAD_svelte-164h06_START -->${$$result.title = `<title>Support Tickets - Admin Dashboard</title>`, ""}<!-- HEAD_svelte-164h06_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm" data-svelte-h="svelte-1nqrqc8"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">Support Management</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Manage customer support tickets and inquiries</p></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="grid grid-cols-1 md:grid-cols-4 gap-4"><div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"><div class="flex items-center justify-between"><div><p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-kovnf2">Open Tickets</p> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(stats.open)}</p></div> <div class="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">${validate_component(Circle_alert, "AlertCircle").$$render(
    $$result,
    {
      class: "h-6 w-6 text-yellow-600 dark:text-yellow-400"
    },
    {},
    {}
  )}</div></div></div> <div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"><div class="flex items-center justify-between"><div><p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1raa8al">In Progress</p> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(stats.inProgress)}</p></div> <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">${validate_component(Clock, "Clock").$$render(
    $$result,
    {
      class: "h-6 w-6 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )}</div></div></div> <div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"><div class="flex items-center justify-between"><div><p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1vto1qm">Resolved Today</p> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(stats.resolved)}</p></div> <div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">${validate_component(Circle_check_big, "CheckCircle").$$render(
    $$result,
    {
      class: "h-6 w-6 text-green-600 dark:text-green-400"
    },
    {},
    {}
  )}</div></div></div> <div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"><div class="flex items-center justify-between"><div><p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-tq8kko">Avg Response</p> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(stats.avgResponseTime)}</p></div> <div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">${validate_component(Message_square, "MessageSquare").$$render(
    $$result,
    {
      class: "h-6 w-6 text-purple-600 dark:text-purple-400"
    },
    {},
    {}
  )}</div></div></div></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-4"><div class="flex flex-col md:flex-row gap-4"><div class="flex-1 relative"><input type="text" placeholder="Search tickets..." class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"${add_attribute("value", searchQuery, 0)}> ${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400"
    },
    {},
    {}
  )}</div> <select class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"><option value="all" data-svelte-h="svelte-rskcdc">All Status</option><option value="open" data-svelte-h="svelte-14z723y">Open</option><option value="in_progress" data-svelte-h="svelte-7y42mr">In Progress</option><option value="resolved" data-svelte-h="svelte-1tursri">Resolved</option><option value="closed" data-svelte-h="svelte-106rur2">Closed</option></select> <select class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"><option value="all" data-svelte-h="svelte-1c1d6wy">All Priorities</option><option value="urgent" data-svelte-h="svelte-pwtzze">Urgent</option><option value="high" data-svelte-h="svelte-poeh2m">High</option><option value="medium" data-svelte-h="svelte-1u6j0ru">Medium</option><option value="low" data-svelte-h="svelte-1f4z4ku">Low</option></select></div></div>  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">${`<div class="bg-white dark:bg-gray-800 shadow-sm rounded-lg overflow-hidden"><table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700"><thead class="bg-gray-50 dark:bg-gray-900" data-svelte-h="svelte-1lgvqpg"><tr><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ticket</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Priority</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Assigned To</th> <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Updated</th> <th class="relative px-6 py-3"><span class="sr-only">Actions</span></th></tr></thead> <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">${each(filteredTickets, (ticket) => {
    return `<tr class="hover:bg-gray-50 dark:hover:bg-gray-700"><td class="px-6 py-4 whitespace-nowrap"><div><p class="text-sm font-medium text-gray-900 dark:text-white">${escape(ticket.id)}</p> <p class="text-sm text-gray-600 dark:text-gray-400 truncate max-w-xs">${escape(ticket.subject)}</p> </div></td> <td class="px-6 py-4 whitespace-nowrap"><div class="flex items-center"><div class="flex-shrink-0 h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">${validate_component(User, "User").$$render(
      $$result,
      {
        class: "h-4 w-4 text-gray-500 dark:text-gray-400"
      },
      {},
      {}
    )}</div> <div class="ml-3"><p class="text-sm font-medium text-gray-900 dark:text-white">${escape(ticket.user.name)}</p> <p class="text-xs text-gray-500 dark:text-gray-400">${escape(ticket.user.tier)} </p></div> </div></td> <td class="px-6 py-4 whitespace-nowrap"><span class="${"inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full " + escape(getStatusColor(ticket.status), true)}">${validate_component(getStatusIcon(ticket.status) || missing_component, "svelte:component").$$render($$result, { class: "h-3 w-3" }, {}, {})} ${escape(ticket.status.replace("_", " "))} </span></td> <td class="px-6 py-4 whitespace-nowrap"><span class="${"text-sm font-medium capitalize " + escape(getPriorityColor(ticket.priority), true)}">${escape(ticket.priority)} </span></td> <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${escape(ticket.assignedTo || "Unassigned")}</td> <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${escape(formatTime(ticket.updatedAt))}</td> <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium"><a href="${"/admin/support/" + escape(ticket.id, true)}" class="text-blue-600 dark:text-blue-400 hover:underline">View
									</a></td> </tr>`;
  })}</tbody></table> ${filteredTickets.length === 0 ? `<div class="text-center py-12">${validate_component(Message_square, "MessageSquare").$$render(
    $$result,
    {
      class: "h-12 w-12 text-gray-400 mx-auto mb-4"
    },
    {},
    {}
  )} <p class="text-gray-500 dark:text-gray-400" data-svelte-h="svelte-1pmqmpc">No tickets found</p></div>` : ``}</div>`}</div></div>`;
});
export {
  Page as default
};
