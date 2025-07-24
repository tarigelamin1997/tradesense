import { c as create_ssr_component, v as validate_component, e as each, a as add_attribute, b as escape, m as missing_component } from "../../../../chunks/ssr.js";
import { B as Bell } from "../../../../chunks/bell.js";
import { M as Mail } from "../../../../chunks/mail.js";
import { S as Smartphone } from "../../../../chunks/smartphone.js";
import { M as Message_square } from "../../../../chunks/message-square.js";
import { M as Monitor, V as Volume_2 } from "../../../../chunks/volume-2.js";
import { T as Trending_up } from "../../../../chunks/trending-up.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let preferences = {
    email: {
      enabled: true,
      trades: true,
      performance: true,
      insights: false,
      system: true,
      frequency: "realtime"
    },
    push: {
      enabled: true,
      trades: true,
      performance: false,
      insights: true,
      system: true
    },
    sms: {
      enabled: false,
      trades: false,
      alerts: false,
      phoneNumber: ""
    },
    desktop: {
      enabled: true,
      sound: true,
      trades: true,
      alerts: true
    },
    trading: {
      priceAlerts: true,
      stopLoss: true,
      takeProfit: true,
      largePositions: true,
      threshold: 1e3
    }
  };
  const channels = [
    {
      id: "email",
      name: "Email Notifications",
      description: "Receive updates via email",
      icon: Mail,
      color: "blue"
    },
    {
      id: "push",
      name: "Push Notifications",
      description: "Mobile app notifications",
      icon: Smartphone,
      color: "green"
    },
    {
      id: "sms",
      name: "SMS Alerts",
      description: "Critical alerts via text",
      icon: Message_square,
      color: "purple"
    },
    {
      id: "desktop",
      name: "Desktop Notifications",
      description: "Browser notifications",
      icon: Monitor,
      color: "orange"
    }
  ];
  return `${$$result.head += `<!-- HEAD_svelte-13vmcmg_START -->${$$result.title = `<title>Notifications - Settings</title>`, ""}<meta name="description" content="Manage your TradeSense notification preferences."><!-- HEAD_svelte-13vmcmg_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-white dark:bg-gray-800 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="flex items-center justify-between"><div class="flex items-center gap-3">${validate_component(Bell, "Bell").$$render(
    $$result,
    {
      class: "h-6 w-6 text-gray-600 dark:text-gray-400"
    },
    {},
    {}
  )} <div data-svelte-h="svelte-1niydbj"><h1 class="text-2xl font-bold text-gray-900 dark:text-white">Notifications</h1> <p class="text-gray-600 dark:text-gray-400 mt-1">Control how and when you receive updates</p></div></div> <button ${""} class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">${`${`Save Changes`}`}</button></div></div></div> <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"> <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">${each(channels, (channel) => {
    return `<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><div class="flex items-start justify-between mb-4"><div class="flex items-center gap-3"><div class="${"p-2 bg-" + escape(channel.color, true) + "-100 dark:bg-" + escape(channel.color, true) + "-900/30 rounded-lg"}">${validate_component(channel.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-6 w-6 text-" + channel.color + "-600 dark:text-" + channel.color + "-400"
      },
      {},
      {}
    )}</div> <div><h3 class="font-semibold text-gray-900 dark:text-white">${escape(channel.name)}</h3> <p class="text-sm text-gray-600 dark:text-gray-400">${escape(channel.description)}</p> </div></div> <label class="relative inline-flex items-center cursor-pointer"><input type="checkbox" class="sr-only peer"${add_attribute("checked", preferences[channel.id].enabled, 1)}> <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div> </label></div> ${channel.id === "email" ? `<div class="space-y-3 pt-2"><label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-nijftn">Trade confirmations</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.email.trades, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-9hi77k">Daily performance</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.email.performance, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-1654sr0">AI insights</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.email.insights, 1)}></label> <div class="pt-2"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1llk6zi">Email frequency</label> <select ${""} class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"><option value="realtime" data-svelte-h="svelte-w3omp5">Real-time</option><option value="hourly" data-svelte-h="svelte-1mv18pc">Hourly digest</option><option value="daily" data-svelte-h="svelte-o5lm5i">Daily digest</option><option value="weekly" data-svelte-h="svelte-10s4zjm">Weekly summary</option></select></div> </div>` : ``} ${channel.id === "push" ? `<div class="space-y-3 pt-2"><label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-4gzktz">Trade updates</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.push.trades, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-j94cls">Performance milestones</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.push.performance, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-1654sr0">AI insights</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.push.insights, 1)}></label> </div>` : ``} ${channel.id === "sms" ? `<div class="space-y-3 pt-2"><div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1t3dnkz">Phone number</label> <input type="tel" ${"disabled"} placeholder="+1 (555) 123-4567" class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"${add_attribute("value", preferences.sms.phoneNumber, 0)}></div> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-zj97h">Critical trade alerts</span> <input type="checkbox" ${"disabled"} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.sms.trades, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-8f7m8h">Risk alerts</span> <input type="checkbox" ${"disabled"} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.sms.alerts, 1)}></label> </div>` : ``} ${channel.id === "desktop" ? `<div class="space-y-3 pt-2"><label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-17tit2w">Play sound</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.desktop.sound, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-nijftn">Trade confirmations</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.desktop.trades, 1)}></label> <label class="flex items-center justify-between"><span class="text-sm text-gray-700 dark:text-gray-300" data-svelte-h="svelte-1m89fgf">Price alerts</span> <input type="checkbox" ${""} class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.desktop.alerts, 1)}></label> <button ${""} class="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed">Test Desktop Notification</button> </div>` : ``} </div>`;
  })}</div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-8"><div class="flex items-center gap-3 mb-6"><div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">${validate_component(Trending_up, "TrendingUp").$$render(
    $$result,
    {
      class: "h-6 w-6 text-red-600 dark:text-red-400"
    },
    {},
    {}
  )}</div> <div data-svelte-h="svelte-1hcdie8"><h3 class="font-semibold text-gray-900 dark:text-white">Trading Alerts</h3> <p class="text-sm text-gray-600 dark:text-gray-400">Get notified about important trading events</p></div></div> <div class="grid grid-cols-1 md:grid-cols-2 gap-6"><div class="space-y-4"><label class="flex items-center justify-between"><div data-svelte-h="svelte-1v09h1q"><span class="text-sm font-medium text-gray-700 dark:text-gray-300">Price alerts</span> <p class="text-xs text-gray-500 dark:text-gray-400">When price targets are reached</p></div> <input type="checkbox" class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.trading.priceAlerts, 1)}></label> <label class="flex items-center justify-between"><div data-svelte-h="svelte-1u0y22n"><span class="text-sm font-medium text-gray-700 dark:text-gray-300">Stop loss triggers</span> <p class="text-xs text-gray-500 dark:text-gray-400">When stop losses are hit</p></div> <input type="checkbox" class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.trading.stopLoss, 1)}></label> <label class="flex items-center justify-between"><div data-svelte-h="svelte-14c4385"><span class="text-sm font-medium text-gray-700 dark:text-gray-300">Take profit alerts</span> <p class="text-xs text-gray-500 dark:text-gray-400">When profit targets are reached</p></div> <input type="checkbox" class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.trading.takeProfit, 1)}></label></div> <div class="space-y-4"><label class="flex items-center justify-between"><div data-svelte-h="svelte-amg1ai"><span class="text-sm font-medium text-gray-700 dark:text-gray-300">Large position alerts</span> <p class="text-xs text-gray-500 dark:text-gray-400">Notify for positions above threshold</p></div> <input type="checkbox" class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"${add_attribute("checked", preferences.trading.largePositions, 1)}></label> ${`<div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-zm2eta">Position size threshold ($)</label> <input type="number" min="100" step="100" class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"${add_attribute("value", preferences.trading.threshold, 0)}></div>`}</div></div></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6"><div class="flex items-center gap-3 mb-6"><div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">${validate_component(Volume_2, "Volume2").$$render(
    $$result,
    {
      class: "h-6 w-6 text-purple-600 dark:text-purple-400"
    },
    {},
    {}
  )}</div> <div data-svelte-h="svelte-1bns2tq"><h3 class="font-semibold text-gray-900 dark:text-white">Quiet Hours</h3> <p class="text-sm text-gray-600 dark:text-gray-400">Pause non-critical notifications during specific times</p></div></div> <div class="flex items-center gap-4" data-svelte-h="svelte-oujw5c"><input type="time" value="22:00" class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"> <span class="text-gray-600 dark:text-gray-400">to</span> <input type="time" value="07:00" class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"></div></div></div></div>`;
});
export {
  Page as default
};
