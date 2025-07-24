import { c as create_ssr_component, e as each, v as validate_component, b as escape, m as missing_component } from "../../../chunks/ssr.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/state.svelte.js";
import { R as Rocket } from "../../../chunks/rocket.js";
import { U as User } from "../../../chunks/user.js";
import { S as Settings } from "../../../chunks/settings.js";
import { U as Upload } from "../../../chunks/upload.js";
import { C as Check } from "../../../chunks/check.js";
import { C as Chart_column } from "../../../chunks/chart-column.js";
import { B as Brain } from "../../../chunks/brain.js";
import { T as Target } from "../../../chunks/target.js";
import { C as Chevron_right } from "../../../chunks/chevron-right.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let currentStepData;
  let progress;
  let currentStep = 1;
  let completedSteps = /* @__PURE__ */ new Set();
  let profileData = {
    displayName: "",
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
  };
  let preferencesData = {
    tradingStyle: ""
  };
  const steps = [
    {
      id: 1,
      title: "Welcome",
      description: "Let's get you started",
      icon: Rocket
    },
    {
      id: 2,
      title: "Profile",
      description: "Tell us about yourself",
      icon: User
    },
    {
      id: 3,
      title: "Preferences",
      description: "Customize your experience",
      icon: Settings
    },
    {
      id: 4,
      title: "Import Trades",
      description: "Bring your trading history",
      icon: Upload
    },
    {
      id: 5,
      title: "Complete",
      description: "You're all set!",
      icon: Check
    }
  ];
  function validateStep() {
    switch (currentStep) {
      case 2:
        return profileData.displayName;
      case 3:
        return preferencesData.tradingStyle;
      default:
        return true;
    }
  }
  currentStepData = steps.find((s) => s.id === currentStep);
  progress = (currentStep - 1) / (steps.length - 1) * 100;
  return `${$$result.head += `<!-- HEAD_svelte-s8v9r_START -->${$$result.title = `<title>Welcome to TradeSense - Setup Your Account</title>`, ""}<!-- HEAD_svelte-s8v9r_END -->`, ""} <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800"><div class="max-w-4xl mx-auto px-4 py-8"> <div class="mb-8"><div class="flex items-center justify-between mb-4"><h1 class="text-2xl font-bold text-gray-900 dark:text-white" data-svelte-h="svelte-19om79h">Account Setup</h1> <button class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white" data-svelte-h="svelte-1qyea1n">Skip for now</button></div> <div class="relative"><div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full"><div class="h-2 bg-blue-600 rounded-full transition-all duration-300" style="${"width: " + escape(progress, true) + "%"}"></div></div>  <div class="absolute -top-3 left-0 right-0 flex justify-between">${each(steps, (step) => {
    return `<div class="${"w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-all " + escape(
      currentStep >= step.id ? "bg-blue-600 text-white" : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400",
      true
    )}">${completedSteps.has(step.id) ? `${validate_component(Check, "Check").$$render($$result, { class: "h-4 w-4" }, {}, {})}` : `${escape(step.id)}`} </div>`;
  })}</div></div></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8"><div class="flex items-center gap-4 mb-6"><div class="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">${validate_component(currentStepData.icon || missing_component, "svelte:component").$$render(
    $$result,
    {
      class: "h-8 w-8 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )}</div> <div><h2 class="text-2xl font-bold text-gray-900 dark:text-white">${escape(currentStepData.title)}</h2> <p class="text-gray-600 dark:text-gray-400">${escape(currentStepData.description)}</p></div></div>  ${` <div class="text-center py-8"><h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-1fn3mga">Welcome to TradeSense! 🎉</h3> <p class="text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto" data-svelte-h="svelte-11h9z3x">We&#39;re excited to have you on board. This quick setup will help us personalize your experience 
						and get you trading smarter in just a few minutes.</p> <div class="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8"><div class="text-center"><div class="inline-flex p-3 bg-green-100 dark:bg-green-900/30 rounded-full mb-3">${validate_component(Chart_column, "BarChart3").$$render(
    $$result,
    {
      class: "h-8 w-8 text-green-600 dark:text-green-400"
    },
    {},
    {}
  )}</div> <h4 class="font-medium text-gray-900 dark:text-white mb-1" data-svelte-h="svelte-1ie7c0q">Track Performance</h4> <p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1h3bgte">Monitor your trades and see detailed analytics</p></div> <div class="text-center"><div class="inline-flex p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full mb-3">${validate_component(Brain, "Brain").$$render(
    $$result,
    {
      class: "h-8 w-8 text-purple-600 dark:text-purple-400"
    },
    {},
    {}
  )}</div> <h4 class="font-medium text-gray-900 dark:text-white mb-1" data-svelte-h="svelte-10y58a0">AI Insights</h4> <p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1qju165">Get personalized recommendations to improve</p></div> <div class="text-center"><div class="inline-flex p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-3">${validate_component(Target, "Target").$$render(
    $$result,
    {
      class: "h-8 w-8 text-blue-600 dark:text-blue-400"
    },
    {},
    {}
  )}</div> <h4 class="font-medium text-gray-900 dark:text-white mb-1" data-svelte-h="svelte-1ls8onc">Achieve Goals</h4> <p class="text-sm text-gray-600 dark:text-gray-400" data-svelte-h="svelte-1at7i2c">Set targets and track your progress</p></div></div></div>`}</div>  <div class="flex items-center justify-between">${`<div></div>`} ${currentStep < steps.length ? `<button ${!validateStep() ? "disabled" : ""} class="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">${escape("Next")} ${validate_component(Chevron_right, "ChevronRight").$$render($$result, { class: "h-5 w-5" }, {}, {})}</button>` : `<button ${""} class="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50">${`Go to Dashboard
						${validate_component(Rocket, "Rocket").$$render($$result, { class: "h-5 w-5" }, {}, {})}`}</button>`}</div></div></div>`;
});
export {
  Page as default
};
