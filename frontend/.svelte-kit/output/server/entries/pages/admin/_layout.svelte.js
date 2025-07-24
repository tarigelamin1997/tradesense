import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, b as escape, e as each, a as add_attribute, v as validate_component } from "../../../chunks/ssr.js";
import { p as page } from "../../../chunks/stores.js";
import { g as goto } from "../../../chunks/client2.js";
import { a as authStore } from "../../../chunks/auth3.js";
import { I as Icon } from "../../../chunks/Icon.js";
const css = {
  code: ".admin-card{background-color:white;border-radius:0.5rem;box-shadow:0 1px 2px 0 rgba(0, 0, 0, 0.05);border:1px solid #e5e7eb;padding:1.5rem}.admin-table{min-width:100%;border-collapse:collapse}.admin-table > * > tr{border-bottom:1px solid #e5e7eb}.admin-table thead{background-color:#f9fafb}.admin-table th{padding:0.75rem 1.5rem;text-align:left;font-size:0.75rem;font-weight:500;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em}.admin-table td{padding:1rem 1.5rem;white-space:nowrap;font-size:0.875rem;color:#111827}",
  map: `{"version":3,"file":"+layout.svelte","sources":["+layout.svelte"],"sourcesContent":["<script>\\n    import { page } from '$app/stores';\\n    import { goto } from '$app/navigation';\\n    import { onMount } from 'svelte';\\n    import { authStore } from '$lib/stores/auth';\\n    import Icon from '$lib/components/Icon.svelte';\\n    \\n    let user = null;\\n    \\n    authStore.subscribe(value => {\\n        user = value.user;\\n        // Redirect if not admin\\n        if (user && user.role !== 'admin') {\\n            goto('/dashboard');\\n        }\\n    });\\n    \\n    onMount(() => {\\n        // Check if user is admin\\n        if (!user || user.role !== 'admin') {\\n            goto('/dashboard');\\n        }\\n    });\\n    \\n    const navigation = [\\n        { href: '/admin', label: 'Dashboard', icon: 'chart-bar' },\\n        { href: '/admin/users', label: 'Users', icon: 'users' },\\n        { href: '/admin/feedback', label: 'Feedback', icon: 'message-square' },\\n        { href: '/admin/analytics', label: 'Analytics', icon: 'chart-line' },\\n        { href: '/admin/support', label: 'Support', icon: 'headset' },\\n        { href: '/admin/settings', label: 'Settings', icon: 'cog' },\\n    ];\\n<\/script>\\n\\n<div class=\\"min-h-screen bg-gray-50\\">\\n    <!-- Admin Header -->\\n    <header class=\\"bg-white shadow-sm border-b border-gray-200\\">\\n        <div class=\\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\\">\\n            <div class=\\"flex justify-between items-center py-4\\">\\n                <div class=\\"flex items-center\\">\\n                    <h1 class=\\"text-2xl font-bold text-gray-900\\">TradeSense Admin</h1>\\n                    <span class=\\"ml-3 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full\\">\\n                        Admin Panel\\n                    </span>\\n                </div>\\n                <div class=\\"flex items-center space-x-4\\">\\n                    <a href=\\"/dashboard\\" class=\\"text-sm text-gray-600 hover:text-gray-900\\">\\n                        Back to App\\n                    </a>\\n                    <div class=\\"h-6 w-px bg-gray-300\\"></div>\\n                    <div class=\\"text-sm text-gray-600\\">\\n                        {user?.email}\\n                    </div>\\n                </div>\\n            </div>\\n        </div>\\n    </header>\\n    \\n    <div class=\\"flex\\">\\n        <!-- Sidebar Navigation -->\\n        <nav class=\\"w-64 bg-white shadow-sm min-h-screen\\">\\n            <div class=\\"p-4\\">\\n                <ul class=\\"space-y-2\\">\\n                    {#each navigation as item}\\n                        <li>\\n                            <a\\n                                href={item.href}\\n                                class=\\"flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors\\n                                       {$page.url.pathname === item.href\\n                                        ? 'bg-indigo-100 text-indigo-700'\\n                                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}\\"\\n                            >\\n                                <Icon name={item.icon} class=\\"w-5 h-5 mr-3\\" />\\n                                {item.label}\\n                            </a>\\n                        </li>\\n                    {/each}\\n                </ul>\\n            </div>\\n            \\n            <!-- Admin Quick Stats -->\\n            <div class=\\"p-4 mt-8 border-t border-gray-200\\">\\n                <h3 class=\\"text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3\\">\\n                    Quick Stats\\n                </h3>\\n                <div class=\\"space-y-3\\">\\n                    <div class=\\"flex justify-between text-sm\\">\\n                        <span class=\\"text-gray-600\\">Total Users</span>\\n                        <span class=\\"font-medium\\">--</span>\\n                    </div>\\n                    <div class=\\"flex justify-between text-sm\\">\\n                        <span class=\\"text-gray-600\\">Active Today</span>\\n                        <span class=\\"font-medium\\">--</span>\\n                    </div>\\n                    <div class=\\"flex justify-between text-sm\\">\\n                        <span class=\\"text-gray-600\\">MRR</span>\\n                        <span class=\\"font-medium\\">--</span>\\n                    </div>\\n                </div>\\n            </div>\\n        </nav>\\n        \\n        <!-- Main Content -->\\n        <main class=\\"flex-1 p-6\\">\\n            <slot />\\n        </main>\\n    </div>\\n</div>\\n\\n<style>\\n    /* Custom admin styles */\\n    :global(.admin-card) {\\n        background-color: white;\\n        border-radius: 0.5rem;\\n        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);\\n        border: 1px solid #e5e7eb;\\n        padding: 1.5rem;\\n    }\\n    \\n    :global(.admin-table) {\\n        min-width: 100%;\\n        border-collapse: collapse;\\n    }\\n    \\n    :global(.admin-table > * > tr) {\\n        border-bottom: 1px solid #e5e7eb;\\n    }\\n    \\n    :global(.admin-table thead) {\\n        background-color: #f9fafb;\\n    }\\n    \\n    :global(.admin-table th) {\\n        padding: 0.75rem 1.5rem;\\n        text-align: left;\\n        font-size: 0.75rem;\\n        font-weight: 500;\\n        color: #6b7280;\\n        text-transform: uppercase;\\n        letter-spacing: 0.05em;\\n    }\\n    \\n    :global(.admin-table td) {\\n        padding: 1rem 1.5rem;\\n        white-space: nowrap;\\n        font-size: 0.875rem;\\n        color: #111827;\\n    }\\n</style>"],"names":[],"mappings":"AA+GY,WAAa,CACjB,gBAAgB,CAAE,KAAK,CACvB,aAAa,CAAE,MAAM,CACrB,UAAU,CAAE,CAAC,CAAC,GAAG,CAAC,GAAG,CAAC,CAAC,CAAC,KAAK,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,IAAI,CAAC,CAC3C,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,OAAO,CACzB,OAAO,CAAE,MACb,CAEQ,YAAc,CAClB,SAAS,CAAE,IAAI,CACf,eAAe,CAAE,QACrB,CAEQ,qBAAuB,CAC3B,aAAa,CAAE,GAAG,CAAC,KAAK,CAAC,OAC7B,CAEQ,kBAAoB,CACxB,gBAAgB,CAAE,OACtB,CAEQ,eAAiB,CACrB,OAAO,CAAE,OAAO,CAAC,MAAM,CACvB,UAAU,CAAE,IAAI,CAChB,SAAS,CAAE,OAAO,CAClB,WAAW,CAAE,GAAG,CAChB,KAAK,CAAE,OAAO,CACd,cAAc,CAAE,SAAS,CACzB,cAAc,CAAE,MACpB,CAEQ,eAAiB,CACrB,OAAO,CAAE,IAAI,CAAC,MAAM,CACpB,WAAW,CAAE,MAAM,CACnB,SAAS,CAAE,QAAQ,CACnB,KAAK,CAAE,OACX"}`
};
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let user = null;
  authStore.subscribe((value) => {
    user = value.user;
    if (user && user.role !== "admin") {
      goto();
    }
  });
  const navigation = [
    {
      href: "/admin",
      label: "Dashboard",
      icon: "chart-bar"
    },
    {
      href: "/admin/users",
      label: "Users",
      icon: "users"
    },
    {
      href: "/admin/feedback",
      label: "Feedback",
      icon: "message-square"
    },
    {
      href: "/admin/analytics",
      label: "Analytics",
      icon: "chart-line"
    },
    {
      href: "/admin/support",
      label: "Support",
      icon: "headset"
    },
    {
      href: "/admin/settings",
      label: "Settings",
      icon: "cog"
    }
  ];
  $$result.css.add(css);
  $$unsubscribe_page();
  return `<div class="min-h-screen bg-gray-50"> <header class="bg-white shadow-sm border-b border-gray-200"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div class="flex justify-between items-center py-4"><div class="flex items-center" data-svelte-h="svelte-39eih5"><h1 class="text-2xl font-bold text-gray-900">TradeSense Admin</h1> <span class="ml-3 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Admin Panel</span></div> <div class="flex items-center space-x-4"><a href="/dashboard" class="text-sm text-gray-600 hover:text-gray-900" data-svelte-h="svelte-1woidry">Back to App</a> <div class="h-6 w-px bg-gray-300"></div> <div class="text-sm text-gray-600">${escape(user?.email)}</div></div></div></div></header> <div class="flex"> <nav class="w-64 bg-white shadow-sm min-h-screen"><div class="p-4"><ul class="space-y-2">${each(navigation, (item) => {
    return `<li><a${add_attribute("href", item.href, 0)} class="${"flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors " + escape(
      $page.url.pathname === item.href ? "bg-indigo-100 text-indigo-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
      true
    )}">${validate_component(Icon, "Icon").$$render($$result, { name: item.icon, class: "w-5 h-5 mr-3" }, {}, {})} ${escape(item.label)}</a> </li>`;
  })}</ul></div>  <div class="p-4 mt-8 border-t border-gray-200" data-svelte-h="svelte-1110k7e"><h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Quick Stats</h3> <div class="space-y-3"><div class="flex justify-between text-sm"><span class="text-gray-600">Total Users</span> <span class="font-medium">--</span></div> <div class="flex justify-between text-sm"><span class="text-gray-600">Active Today</span> <span class="font-medium">--</span></div> <div class="flex justify-between text-sm"><span class="text-gray-600">MRR</span> <span class="font-medium">--</span></div></div></div></nav>  <main class="flex-1 p-6">${slots.default ? slots.default({}) : ``}</main></div> </div>`;
});
export {
  Layout as default
};
