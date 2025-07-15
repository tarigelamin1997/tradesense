import { s as subscribe } from "../../chunks/utils.js";
import { c as create_ssr_component, v as validate_component, a as add_attribute, e as each, b as escape, m as missing_component } from "../../chunks/ssr.js";
import { i as isAuthenticated, a as auth } from "../../chunks/auth.js";
import "../../chunks/client.js";
import { w as websocket, a as wsConnected } from "../../chunks/websocket.js";
import { I as Icon } from "../../chunks/Icon.js";
import { C as Circle_alert, F as File_text } from "../../chunks/file-text.js";
import { p as page } from "../../chunks/stores.js";
import { T as Trending_up } from "../../chunks/trending-up.js";
import { d as derived, w as writable } from "../../chunks/index.js";
const Bell = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M10.268 21a2 2 0 0 0 3.464 0" }],
    [
      "path",
      {
        "d": "M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bell" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Chart_no_axes_column = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "line",
      {
        "x1": "18",
        "x2": "18",
        "y1": "20",
        "y2": "10"
      }
    ],
    [
      "line",
      {
        "x1": "12",
        "x2": "12",
        "y1": "20",
        "y2": "4"
      }
    ],
    [
      "line",
      {
        "x1": "6",
        "x2": "6",
        "y1": "20",
        "y2": "14"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "chart-no-axes-column" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const House = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"
      }
    ],
    [
      "path",
      {
        "d": "M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "house" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Menu = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M4 12h16" }],
    ["path", { "d": "M4 18h16" }],
    ["path", { "d": "M4 6h16" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "menu" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Wifi_off = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M12 20h.01" }],
    ["path", { "d": "M8.5 16.429a5 5 0 0 1 7 0" }],
    ["path", { "d": "M5 12.859a10 10 0 0 1 5.17-2.69" }],
    [
      "path",
      {
        "d": "M19 12.859a10 10 0 0 0-2.007-1.523"
      }
    ],
    ["path", { "d": "M2 8.82a15 15 0 0 1 4.177-2.643" }],
    ["path", { "d": "M22 8.82a15 15 0 0 0-11.288-3.764" }],
    ["path", { "d": "m2 2 20 20" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "wifi-off" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Wifi = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "M12 20h.01" }],
    ["path", { "d": "M2 8.82a15 15 0 0 1 20 0" }],
    ["path", { "d": "M5 12.859a10 10 0 0 1 14 0" }],
    ["path", { "d": "M8.5 16.429a5 5 0 0 1 7 0" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "wifi" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const css$4 = {
  code: ".ws-status.svelte-ulvmx0{display:flex;align-items:center;gap:0.5rem;padding:0.5rem 1rem;background:#fee;color:#dc2626;border-radius:20px;font-size:0.875rem;font-weight:500;transition:all 0.3s}.ws-status.connected.svelte-ulvmx0{background:#d1fae5;color:#059669}.spinner.svelte-ulvmx0{width:16px;height:16px;border:2px solid #f3f4f6;border-top-color:#3b82f6;border-radius:50%;animation:svelte-ulvmx0-spin 1s linear infinite}@keyframes svelte-ulvmx0-spin{to{transform:rotate(360deg)}}",
  map: `{"version":3,"file":"WebSocketStatus.svelte","sources":["WebSocketStatus.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { websocket, wsConnected } from \\"$lib/stores/websocket\\";\\nimport { Wifi, WifiOff, AlertCircle } from \\"lucide-svelte\\";\\n$: status = $websocket.status;\\n$: error = $websocket.error;\\n<\/script>\\n\\n<div class=\\"ws-status\\" class:connected={$wsConnected}>\\n\\t{#if status === 'connected'}\\n\\t\\t<Wifi size={16} />\\n\\t\\t<span>Live</span>\\n\\t{:else if status === 'connecting'}\\n\\t\\t<div class=\\"spinner\\" />\\n\\t\\t<span>Connecting...</span>\\n\\t{:else if status === 'error'}\\n\\t\\t<AlertCircle size={16} />\\n\\t\\t<span title={error || 'Connection error'}>Error</span>\\n\\t{:else}\\n\\t\\t<WifiOff size={16} />\\n\\t\\t<span>Offline</span>\\n\\t{/if}\\n</div>\\n\\n<style>\\n\\t.ws-status {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tgap: 0.5rem;\\n\\t\\tpadding: 0.5rem 1rem;\\n\\t\\tbackground: #fee;\\n\\t\\tcolor: #dc2626;\\n\\t\\tborder-radius: 20px;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tfont-weight: 500;\\n\\t\\ttransition: all 0.3s;\\n\\t}\\n\\t\\n\\t.ws-status.connected {\\n\\t\\tbackground: #d1fae5;\\n\\t\\tcolor: #059669;\\n\\t}\\n\\t\\n\\t.spinner {\\n\\t\\twidth: 16px;\\n\\t\\theight: 16px;\\n\\t\\tborder: 2px solid #f3f4f6;\\n\\t\\tborder-top-color: #3b82f6;\\n\\t\\tborder-radius: 50%;\\n\\t\\tanimation: spin 1s linear infinite;\\n\\t}\\n\\t\\n\\t@keyframes spin {\\n\\t\\tto {\\n\\t\\t\\ttransform: rotate(360deg);\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"AAuBC,wBAAW,CACV,OAAO,CAAE,IAAI,CACb,WAAW,CAAE,MAAM,CACnB,GAAG,CAAE,MAAM,CACX,OAAO,CAAE,MAAM,CAAC,IAAI,CACpB,UAAU,CAAE,IAAI,CAChB,KAAK,CAAE,OAAO,CACd,aAAa,CAAE,IAAI,CACnB,SAAS,CAAE,QAAQ,CACnB,WAAW,CAAE,GAAG,CAChB,UAAU,CAAE,GAAG,CAAC,IACjB,CAEA,UAAU,wBAAW,CACpB,UAAU,CAAE,OAAO,CACnB,KAAK,CAAE,OACR,CAEA,sBAAS,CACR,KAAK,CAAE,IAAI,CACX,MAAM,CAAE,IAAI,CACZ,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,OAAO,CACzB,gBAAgB,CAAE,OAAO,CACzB,aAAa,CAAE,GAAG,CAClB,SAAS,CAAE,kBAAI,CAAC,EAAE,CAAC,MAAM,CAAC,QAC3B,CAEA,WAAW,kBAAK,CACf,EAAG,CACF,SAAS,CAAE,OAAO,MAAM,CACzB,CACD"}`
};
const WebSocketStatus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let status;
  let error;
  let $websocket, $$unsubscribe_websocket;
  let $wsConnected, $$unsubscribe_wsConnected;
  $$unsubscribe_websocket = subscribe(websocket, (value) => $websocket = value);
  $$unsubscribe_wsConnected = subscribe(wsConnected, (value) => $wsConnected = value);
  $$result.css.add(css$4);
  status = $websocket.status;
  error = $websocket.error;
  $$unsubscribe_websocket();
  $$unsubscribe_wsConnected();
  return `<div class="${["ws-status svelte-ulvmx0", $wsConnected ? "connected" : ""].join(" ").trim()}">${status === "connected" ? `${validate_component(Wifi, "Wifi").$$render($$result, { size: 16 }, {}, {})} <span data-svelte-h="svelte-rr9roo">Live</span>` : `${status === "connecting" ? `<div class="spinner svelte-ulvmx0"></div> <span data-svelte-h="svelte-zvx9gy">Connecting...</span>` : `${status === "error" ? `${validate_component(Circle_alert, "AlertCircle").$$render($$result, { size: 16 }, {}, {})} <span${add_attribute("title", error || "Connection error", 0)}>Error</span>` : `${validate_component(Wifi_off, "WifiOff").$$render($$result, { size: 16 }, {}, {})} <span data-svelte-h="svelte-yyddyf">Offline</span>`}`}`} </div>`;
});
const css$3 = {
  code: ".mobile-nav.svelte-clzebw.svelte-clzebw{position:fixed;bottom:0;left:0;right:0;background:white;border-top:1px solid #e0e0e0;display:none;z-index:100;padding-bottom:env(safe-area-inset-bottom)}@media(max-width: 768px){.mobile-nav.svelte-clzebw.svelte-clzebw{display:flex;justify-content:space-around;align-items:center;height:60px}}.nav-item.svelte-clzebw.svelte-clzebw{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.25rem;padding:0.5rem;color:#666;text-decoration:none;font-size:0.75rem;transition:color 0.2s;flex:1;background:none;border:none;cursor:pointer}.nav-item.svelte-clzebw.svelte-clzebw:active{background:#f3f4f6}.nav-item.active.svelte-clzebw.svelte-clzebw{color:#10b981}.nav-item.svelte-clzebw span.svelte-clzebw{margin-top:0.125rem}.menu-overlay.svelte-clzebw.svelte-clzebw{position:fixed;inset:0;background:rgba(0, 0, 0, 0.5);z-index:200;animation:svelte-clzebw-fadeIn 0.2s}@keyframes svelte-clzebw-fadeIn{from{opacity:0}to{opacity:1}}.menu-content.svelte-clzebw.svelte-clzebw{position:absolute;right:0;top:0;bottom:0;width:280px;max-width:80vw;background:white;padding:1.5rem;box-shadow:-2px 0 8px rgba(0, 0, 0, 0.1);animation:svelte-clzebw-slideIn 0.3s;display:flex;flex-direction:column}@keyframes svelte-clzebw-slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}.menu-header.svelte-clzebw.svelte-clzebw{display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem}.menu-header.svelte-clzebw h2.svelte-clzebw{font-size:1.5rem;margin:0}.close-button.svelte-clzebw.svelte-clzebw{background:none;border:none;color:#666;cursor:pointer;padding:0.5rem;margin:-0.5rem}.user-info.svelte-clzebw.svelte-clzebw{display:flex;align-items:center;gap:1rem;padding:1rem;background:#f9fafb;border-radius:8px;margin-bottom:2rem}.user-info.svelte-clzebw svg{color:#666}.username.svelte-clzebw.svelte-clzebw{font-weight:600;margin-bottom:0.25rem}.email.svelte-clzebw.svelte-clzebw{font-size:0.875rem;color:#666}.menu-links.svelte-clzebw.svelte-clzebw{flex:1;display:flex;flex-direction:column;gap:0.5rem}.menu-links.svelte-clzebw a.svelte-clzebw{display:block;padding:0.75rem 1rem;color:#333;text-decoration:none;border-radius:6px;transition:background 0.2s}.menu-links.svelte-clzebw a.svelte-clzebw:hover{background:#f3f4f6}.logout-button.svelte-clzebw.svelte-clzebw{display:flex;align-items:center;justify-content:center;gap:0.5rem;width:100%;padding:0.75rem;background:#fee;color:#dc2626;border:none;border-radius:6px;font-weight:500;cursor:pointer;transition:background 0.2s;margin-top:auto}.logout-button.svelte-clzebw.svelte-clzebw:hover{background:#fecaca}",
  map: `{"version":3,"file":"MobileNav.svelte","sources":["MobileNav.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { Home, TrendingUp, FileText, BarChart2, Menu, X, User, LogOut } from \\"lucide-svelte\\";\\nimport { goto } from \\"$app/navigation\\";\\nimport { page } from \\"$app/stores\\";\\nimport { auth, isAuthenticated } from \\"$lib/api/auth\\";\\nlet isMenuOpen = false;\\nlet authState = { user: null, loading: true, error: null };\\nauth.subscribe((state) => {\\n  authState = state;\\n});\\nasync function handleLogout() {\\n  await auth.logout();\\n  goto(\\"/login\\");\\n  isMenuOpen = false;\\n}\\nfunction toggleMenu() {\\n  isMenuOpen = !isMenuOpen;\\n}\\nfunction closeMenu() {\\n  isMenuOpen = false;\\n}\\n$: currentPath = $page.url.pathname;\\nconst navItems = [\\n  { path: \\"/\\", icon: Home, label: \\"Dashboard\\" },\\n  { path: \\"/tradelog\\", icon: TrendingUp, label: \\"Trade Log\\" },\\n  { path: \\"/journal\\", icon: FileText, label: \\"Journal\\" },\\n  { path: \\"/analytics\\", icon: BarChart2, label: \\"Analytics\\" }\\n];\\n<\/script>\\n\\n{#if $isAuthenticated}\\n\\t<!-- Mobile Bottom Navigation -->\\n\\t<nav class=\\"mobile-nav\\">\\n\\t\\t{#each navItems as item}\\n\\t\\t\\t<a \\n\\t\\t\\t\\thref={item.path} \\n\\t\\t\\t\\tclass=\\"nav-item\\"\\n\\t\\t\\t\\tclass:active={currentPath === item.path}\\n\\t\\t\\t\\ton:click={closeMenu}\\n\\t\\t\\t>\\n\\t\\t\\t\\t<svelte:component this={item.icon} size={20} />\\n\\t\\t\\t\\t<span>{item.label}</span>\\n\\t\\t\\t</a>\\n\\t\\t{/each}\\n\\t\\t<button class=\\"nav-item menu-button\\" on:click={toggleMenu}>\\n\\t\\t\\t<Menu size={20} />\\n\\t\\t\\t<span>Menu</span>\\n\\t\\t</button>\\n\\t</nav>\\n\\t\\n\\t<!-- Mobile Menu Overlay -->\\n\\t{#if isMenuOpen}\\n\\t\\t<div class=\\"menu-overlay\\" on:click={closeMenu}>\\n\\t\\t\\t<div class=\\"menu-content\\" on:click|stopPropagation>\\n\\t\\t\\t\\t<div class=\\"menu-header\\">\\n\\t\\t\\t\\t\\t<h2>TradeSense</h2>\\n\\t\\t\\t\\t\\t<button class=\\"close-button\\" on:click={closeMenu} aria-label=\\"Close menu\\">\\n\\t\\t\\t\\t\\t\\t<X size={24} />\\n\\t\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<div class=\\"user-info\\">\\n\\t\\t\\t\\t\\t<User size={32} />\\n\\t\\t\\t\\t\\t<div>\\n\\t\\t\\t\\t\\t\\t<p class=\\"username\\">{authState?.user?.username || 'User'}</p>\\n\\t\\t\\t\\t\\t\\t<p class=\\"email\\">{authState?.user?.email || ''}</p>\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<div class=\\"menu-links\\">\\n\\t\\t\\t\\t\\t<a href=\\"/playbook\\" on:click={closeMenu}>Playbook</a>\\n\\t\\t\\t\\t\\t<a href=\\"/pricing\\" on:click={closeMenu}>Pricing</a>\\n\\t\\t\\t\\t\\t<a href=\\"/billing\\" on:click={closeMenu}>Billing</a>\\n\\t\\t\\t\\t\\t<a href=\\"/settings\\" on:click={closeMenu}>Settings</a>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<button class=\\"logout-button\\" on:click={handleLogout}>\\n\\t\\t\\t\\t\\t<LogOut size={18} />\\n\\t\\t\\t\\t\\tLog Out\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t{/if}\\n{/if}\\n\\n<style>\\n\\t.mobile-nav {\\n\\t\\tposition: fixed;\\n\\t\\tbottom: 0;\\n\\t\\tleft: 0;\\n\\t\\tright: 0;\\n\\t\\tbackground: white;\\n\\t\\tborder-top: 1px solid #e0e0e0;\\n\\t\\tdisplay: none;\\n\\t\\tz-index: 100;\\n\\t\\tpadding-bottom: env(safe-area-inset-bottom);\\n\\t}\\n\\t\\n\\t@media (max-width: 768px) {\\n\\t\\t.mobile-nav {\\n\\t\\t\\tdisplay: flex;\\n\\t\\t\\tjustify-content: space-around;\\n\\t\\t\\talign-items: center;\\n\\t\\t\\theight: 60px;\\n\\t\\t}\\n\\t}\\n\\t\\n\\t.nav-item {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\tgap: 0.25rem;\\n\\t\\tpadding: 0.5rem;\\n\\t\\tcolor: #666;\\n\\t\\ttext-decoration: none;\\n\\t\\tfont-size: 0.75rem;\\n\\t\\ttransition: color 0.2s;\\n\\t\\tflex: 1;\\n\\t\\tbackground: none;\\n\\t\\tborder: none;\\n\\t\\tcursor: pointer;\\n\\t}\\n\\t\\n\\t.nav-item:active {\\n\\t\\tbackground: #f3f4f6;\\n\\t}\\n\\t\\n\\t.nav-item.active {\\n\\t\\tcolor: #10b981;\\n\\t}\\n\\t\\n\\t.nav-item span {\\n\\t\\tmargin-top: 0.125rem;\\n\\t}\\n\\t\\n\\t/* Menu Overlay */\\n\\t.menu-overlay {\\n\\t\\tposition: fixed;\\n\\t\\tinset: 0;\\n\\t\\tbackground: rgba(0, 0, 0, 0.5);\\n\\t\\tz-index: 200;\\n\\t\\tanimation: fadeIn 0.2s;\\n\\t}\\n\\t\\n\\t@keyframes fadeIn {\\n\\t\\tfrom {\\n\\t\\t\\topacity: 0;\\n\\t\\t}\\n\\t\\tto {\\n\\t\\t\\topacity: 1;\\n\\t\\t}\\n\\t}\\n\\t\\n\\t.menu-content {\\n\\t\\tposition: absolute;\\n\\t\\tright: 0;\\n\\t\\ttop: 0;\\n\\t\\tbottom: 0;\\n\\t\\twidth: 280px;\\n\\t\\tmax-width: 80vw;\\n\\t\\tbackground: white;\\n\\t\\tpadding: 1.5rem;\\n\\t\\tbox-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);\\n\\t\\tanimation: slideIn 0.3s;\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t}\\n\\t\\n\\t@keyframes slideIn {\\n\\t\\tfrom {\\n\\t\\t\\ttransform: translateX(100%);\\n\\t\\t}\\n\\t\\tto {\\n\\t\\t\\ttransform: translateX(0);\\n\\t\\t}\\n\\t}\\n\\t\\n\\t.menu-header {\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: space-between;\\n\\t\\talign-items: center;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.menu-header h2 {\\n\\t\\tfont-size: 1.5rem;\\n\\t\\tmargin: 0;\\n\\t}\\n\\t\\n\\t.close-button {\\n\\t\\tbackground: none;\\n\\t\\tborder: none;\\n\\t\\tcolor: #666;\\n\\t\\tcursor: pointer;\\n\\t\\tpadding: 0.5rem;\\n\\t\\tmargin: -0.5rem;\\n\\t}\\n\\t\\n\\t.user-info {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tgap: 1rem;\\n\\t\\tpadding: 1rem;\\n\\t\\tbackground: #f9fafb;\\n\\t\\tborder-radius: 8px;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.user-info :global(svg) {\\n\\t\\tcolor: #666;\\n\\t}\\n\\t\\n\\t.username {\\n\\t\\tfont-weight: 600;\\n\\t\\tmargin-bottom: 0.25rem;\\n\\t}\\n\\t\\n\\t.email {\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcolor: #666;\\n\\t}\\n\\t\\n\\t.menu-links {\\n\\t\\tflex: 1;\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\tgap: 0.5rem;\\n\\t}\\n\\t\\n\\t.menu-links a {\\n\\t\\tdisplay: block;\\n\\t\\tpadding: 0.75rem 1rem;\\n\\t\\tcolor: #333;\\n\\t\\ttext-decoration: none;\\n\\t\\tborder-radius: 6px;\\n\\t\\ttransition: background 0.2s;\\n\\t}\\n\\t\\n\\t.menu-links a:hover {\\n\\t\\tbackground: #f3f4f6;\\n\\t}\\n\\t\\n\\t.logout-button {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\tgap: 0.5rem;\\n\\t\\twidth: 100%;\\n\\t\\tpadding: 0.75rem;\\n\\t\\tbackground: #fee;\\n\\t\\tcolor: #dc2626;\\n\\t\\tborder: none;\\n\\t\\tborder-radius: 6px;\\n\\t\\tfont-weight: 500;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: background 0.2s;\\n\\t\\tmargin-top: auto;\\n\\t}\\n\\t\\n\\t.logout-button:hover {\\n\\t\\tbackground: #fecaca;\\n\\t}\\n</style>"],"names":[],"mappings":"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"}`
};
const MobileNav = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let currentPath;
  let $page, $$unsubscribe_page;
  let $isAuthenticated, $$unsubscribe_isAuthenticated;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  $$unsubscribe_isAuthenticated = subscribe(isAuthenticated, (value) => $isAuthenticated = value);
  auth.subscribe((state) => {
  });
  const navItems = [
    {
      path: "/",
      icon: House,
      label: "Dashboard"
    },
    {
      path: "/tradelog",
      icon: Trending_up,
      label: "Trade Log"
    },
    {
      path: "/journal",
      icon: File_text,
      label: "Journal"
    },
    {
      path: "/analytics",
      icon: Chart_no_axes_column,
      label: "Analytics"
    }
  ];
  $$result.css.add(css$3);
  currentPath = $page.url.pathname;
  $$unsubscribe_page();
  $$unsubscribe_isAuthenticated();
  return `${$isAuthenticated ? ` <nav class="mobile-nav svelte-clzebw">${each(navItems, (item) => {
    return `<a${add_attribute("href", item.path, 0)} class="${["nav-item svelte-clzebw", currentPath === item.path ? "active" : ""].join(" ").trim()}">${validate_component(item.icon || missing_component, "svelte:component").$$render($$result, { size: 20 }, {}, {})} <span class="svelte-clzebw">${escape(item.label)}</span> </a>`;
  })} <button class="nav-item menu-button svelte-clzebw">${validate_component(Menu, "Menu").$$render($$result, { size: 20 }, {}, {})} <span class="svelte-clzebw" data-svelte-h="svelte-k09699">Menu</span></button></nav>  ${``}` : ``}`;
});
const css$2 = {
  code: ".install-prompt.svelte-1ll3m3.svelte-1ll3m3{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:1000;animation:svelte-1ll3m3-slideUp 0.3s ease-out;max-width:90vw;width:100%}@keyframes svelte-1ll3m3-slideUp{from{transform:translateX(-50%) translateY(100%);opacity:0}to{transform:translateX(-50%) translateY(0);opacity:1}}.prompt-content.svelte-1ll3m3.svelte-1ll3m3{background:white;border-radius:12px;box-shadow:0 4px 24px rgba(0, 0, 0, 0.15);padding:1.5rem;position:relative;max-width:400px;margin:0 auto}.close-button.svelte-1ll3m3.svelte-1ll3m3{position:absolute;top:0.75rem;right:0.75rem;background:none;border:none;color:#666;cursor:pointer;padding:0.25rem;border-radius:4px;transition:all 0.2s}.close-button.svelte-1ll3m3.svelte-1ll3m3:hover{background:#f3f4f6;color:#333}.prompt-icon.svelte-1ll3m3.svelte-1ll3m3{display:flex;align-items:center;justify-content:center;width:48px;height:48px;background:#f0fdf4;border-radius:12px;margin-bottom:1rem;color:#10b981}.prompt-text.svelte-1ll3m3 h3.svelte-1ll3m3{margin:0 0 0.25rem;font-size:1.125rem;color:#1a1a1a}.prompt-text.svelte-1ll3m3 p.svelte-1ll3m3{margin:0;font-size:0.875rem;color:#666}.prompt-actions.svelte-1ll3m3.svelte-1ll3m3{display:flex;gap:0.75rem;margin-top:1.5rem}.dismiss-button.svelte-1ll3m3.svelte-1ll3m3,.install-button.svelte-1ll3m3.svelte-1ll3m3{flex:1;padding:0.75rem 1rem;border:none;border-radius:6px;font-size:0.875rem;font-weight:500;cursor:pointer;transition:all 0.2s}.dismiss-button.svelte-1ll3m3.svelte-1ll3m3{background:#f3f4f6;color:#666}.dismiss-button.svelte-1ll3m3.svelte-1ll3m3:hover{background:#e5e7eb;color:#333}.install-button.svelte-1ll3m3.svelte-1ll3m3{background:#10b981;color:white}.install-button.svelte-1ll3m3.svelte-1ll3m3:hover{background:#059669;transform:translateY(-1px);box-shadow:0 2px 8px rgba(16, 185, 129, 0.3)}@media(max-width: 768px){.install-prompt.svelte-1ll3m3.svelte-1ll3m3{bottom:70px}}@media(max-width: 640px){.prompt-content.svelte-1ll3m3.svelte-1ll3m3{padding:1.25rem}.prompt-icon.svelte-1ll3m3.svelte-1ll3m3{width:40px;height:40px}.prompt-text.svelte-1ll3m3 h3.svelte-1ll3m3{font-size:1rem}.prompt-text.svelte-1ll3m3 p.svelte-1ll3m3{font-size:0.8125rem}}",
  map: `{"version":3,"file":"PWAInstallPrompt.svelte","sources":["PWAInstallPrompt.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { onMount } from \\"svelte\\";\\nimport { X, Download } from \\"lucide-svelte\\";\\nlet deferredPrompt = null;\\nlet showPrompt = false;\\nlet isInstalled = false;\\nonMount(() => {\\n  if (window.matchMedia(\\"(display-mode: standalone)\\").matches) {\\n    isInstalled = true;\\n    return;\\n  }\\n  window.addEventListener(\\"beforeinstallprompt\\", (e) => {\\n    e.preventDefault();\\n    deferredPrompt = e;\\n    setTimeout(() => {\\n      showPrompt = true;\\n    }, 3e4);\\n  });\\n  window.addEventListener(\\"appinstalled\\", () => {\\n    showPrompt = false;\\n    deferredPrompt = null;\\n    isInstalled = true;\\n  });\\n  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);\\n  if (isIOS && !isInstalled) {\\n    setTimeout(() => {\\n      showPrompt = true;\\n    }, 6e4);\\n  }\\n});\\nasync function handleInstall() {\\n  if (!deferredPrompt) {\\n    alert('To install TradeSense on iOS:\\\\n1. Tap the Share button\\\\n2. Select \\"Add to Home Screen\\"\\\\n3. Tap \\"Add\\"');\\n    return;\\n  }\\n  deferredPrompt.prompt();\\n  const { outcome } = await deferredPrompt.userChoice;\\n  if (outcome === \\"accepted\\") {\\n    console.log(\\"User accepted the install prompt\\");\\n  }\\n  deferredPrompt = null;\\n  showPrompt = false;\\n}\\nfunction handleDismiss() {\\n  showPrompt = false;\\n  localStorage.setItem(\\"pwa-prompt-dismissed\\", Date.now().toString());\\n}\\nonMount(() => {\\n  const dismissed = localStorage.getItem(\\"pwa-prompt-dismissed\\");\\n  if (dismissed) {\\n    const dismissedTime = parseInt(dismissed);\\n    const daysSince = (Date.now() - dismissedTime) / (1e3 * 60 * 60 * 24);\\n    if (daysSince < 7) {\\n      showPrompt = false;\\n    }\\n  }\\n});\\n<\/script>\\n\\n{#if showPrompt && !isInstalled}\\n\\t<div class=\\"install-prompt\\">\\n\\t\\t<div class=\\"prompt-content\\">\\n\\t\\t\\t<button class=\\"close-button\\" on:click={handleDismiss}>\\n\\t\\t\\t\\t<X size={18} />\\n\\t\\t\\t</button>\\n\\t\\t\\t\\n\\t\\t\\t<div class=\\"prompt-icon\\">\\n\\t\\t\\t\\t<Download size={24} />\\n\\t\\t\\t</div>\\n\\t\\t\\t\\n\\t\\t\\t<div class=\\"prompt-text\\">\\n\\t\\t\\t\\t<h3>Install TradeSense</h3>\\n\\t\\t\\t\\t<p>Add to your home screen for a better experience</p>\\n\\t\\t\\t</div>\\n\\t\\t\\t\\n\\t\\t\\t<div class=\\"prompt-actions\\">\\n\\t\\t\\t\\t<button class=\\"dismiss-button\\" on:click={handleDismiss}>\\n\\t\\t\\t\\t\\tNot now\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t<button class=\\"install-button\\" on:click={handleInstall}>\\n\\t\\t\\t\\t\\tInstall\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t</div>\\n{/if}\\n\\n<style>\\n\\t.install-prompt {\\n\\t\\tposition: fixed;\\n\\t\\tbottom: 20px;\\n\\t\\tleft: 50%;\\n\\t\\ttransform: translateX(-50%);\\n\\t\\tz-index: 1000;\\n\\t\\tanimation: slideUp 0.3s ease-out;\\n\\t\\tmax-width: 90vw;\\n\\t\\twidth: 100%;\\n\\t}\\n\\t\\n\\t@keyframes slideUp {\\n\\t\\tfrom {\\n\\t\\t\\ttransform: translateX(-50%) translateY(100%);\\n\\t\\t\\topacity: 0;\\n\\t\\t}\\n\\t\\tto {\\n\\t\\t\\ttransform: translateX(-50%) translateY(0);\\n\\t\\t\\topacity: 1;\\n\\t\\t}\\n\\t}\\n\\t\\n\\t.prompt-content {\\n\\t\\tbackground: white;\\n\\t\\tborder-radius: 12px;\\n\\t\\tbox-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);\\n\\t\\tpadding: 1.5rem;\\n\\t\\tposition: relative;\\n\\t\\tmax-width: 400px;\\n\\t\\tmargin: 0 auto;\\n\\t}\\n\\t\\n\\t.close-button {\\n\\t\\tposition: absolute;\\n\\t\\ttop: 0.75rem;\\n\\t\\tright: 0.75rem;\\n\\t\\tbackground: none;\\n\\t\\tborder: none;\\n\\t\\tcolor: #666;\\n\\t\\tcursor: pointer;\\n\\t\\tpadding: 0.25rem;\\n\\t\\tborder-radius: 4px;\\n\\t\\ttransition: all 0.2s;\\n\\t}\\n\\t\\n\\t.close-button:hover {\\n\\t\\tbackground: #f3f4f6;\\n\\t\\tcolor: #333;\\n\\t}\\n\\t\\n\\t.prompt-icon {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\twidth: 48px;\\n\\t\\theight: 48px;\\n\\t\\tbackground: #f0fdf4;\\n\\t\\tborder-radius: 12px;\\n\\t\\tmargin-bottom: 1rem;\\n\\t\\tcolor: #10b981;\\n\\t}\\n\\t\\n\\t.prompt-text h3 {\\n\\t\\tmargin: 0 0 0.25rem;\\n\\t\\tfont-size: 1.125rem;\\n\\t\\tcolor: #1a1a1a;\\n\\t}\\n\\t\\n\\t.prompt-text p {\\n\\t\\tmargin: 0;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcolor: #666;\\n\\t}\\n\\t\\n\\t.prompt-actions {\\n\\t\\tdisplay: flex;\\n\\t\\tgap: 0.75rem;\\n\\t\\tmargin-top: 1.5rem;\\n\\t}\\n\\t\\n\\t.dismiss-button,\\n\\t.install-button {\\n\\t\\tflex: 1;\\n\\t\\tpadding: 0.75rem 1rem;\\n\\t\\tborder: none;\\n\\t\\tborder-radius: 6px;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tfont-weight: 500;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: all 0.2s;\\n\\t}\\n\\t\\n\\t.dismiss-button {\\n\\t\\tbackground: #f3f4f6;\\n\\t\\tcolor: #666;\\n\\t}\\n\\t\\n\\t.dismiss-button:hover {\\n\\t\\tbackground: #e5e7eb;\\n\\t\\tcolor: #333;\\n\\t}\\n\\t\\n\\t.install-button {\\n\\t\\tbackground: #10b981;\\n\\t\\tcolor: white;\\n\\t}\\n\\t\\n\\t.install-button:hover {\\n\\t\\tbackground: #059669;\\n\\t\\ttransform: translateY(-1px);\\n\\t\\tbox-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);\\n\\t}\\n\\t\\n\\t/* Mobile adjustments */\\n\\t@media (max-width: 768px) {\\n\\t\\t.install-prompt {\\n\\t\\t\\tbottom: 70px; /* Above mobile nav */\\n\\t\\t}\\n\\t}\\n\\t\\n\\t@media (max-width: 640px) {\\n\\t\\t.prompt-content {\\n\\t\\t\\tpadding: 1.25rem;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.prompt-icon {\\n\\t\\t\\twidth: 40px;\\n\\t\\t\\theight: 40px;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.prompt-text h3 {\\n\\t\\t\\tfont-size: 1rem;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.prompt-text p {\\n\\t\\t\\tfont-size: 0.8125rem;\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"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"}`
};
const PWAInstallPrompt = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  $$result.css.add(css$2);
  return `${``}`;
});
function createNotificationStore() {
  const { subscribe: subscribe2, set, update } = writable([]);
  let notificationCounter = 0;
  function addNotification(notification) {
    const newNotification = {
      ...notification,
      id: `notif-${Date.now()}-${notificationCounter++}`,
      timestamp: /* @__PURE__ */ new Date(),
      read: false
    };
    update((notifications2) => [newNotification, ...notifications2]);
    if (notification.type !== "error") {
      setTimeout(() => {
        removeNotification(newNotification.id);
      }, 1e4);
    }
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(notification.title, {
        body: notification.message,
        icon: "/favicon.ico"
      });
    }
  }
  function removeNotification(id) {
    update((notifications2) => notifications2.filter((n) => n.id !== id));
  }
  function markAsRead(id) {
    update(
      (notifications2) => notifications2.map(
        (n) => n.id === id ? { ...n, read: true } : n
      )
    );
  }
  function clearAll() {
    set([]);
  }
  websocket.subscribe((ws) => {
    if (ws.lastMessage?.type === "notification") {
      const data = ws.lastMessage.data;
      addNotification({
        type: data.severity || "info",
        title: data.title,
        message: data.message
      });
    }
    if (ws.lastMessage?.type === "trade_update") {
      const data = ws.lastMessage.data;
      const action = data.action || "updated";
      addNotification({
        type: "success",
        title: `Trade ${action}`,
        message: `Trade ${data.trade?.symbol || ""} has been ${action}`
      });
    }
    if (ws.lastMessage?.type === "performance_alert") {
      const data = ws.lastMessage.data;
      addNotification({
        type: data.severity || "warning",
        title: "Performance Alert",
        message: data.message
      });
    }
  });
  return {
    subscribe: subscribe2,
    addNotification,
    removeNotification,
    markAsRead,
    clearAll
  };
}
const notifications = createNotificationStore();
const unreadCount = derived(
  notifications,
  ($notifications) => $notifications.filter((n) => !n.read).length
);
if (typeof window !== "undefined" && "Notification" in window) {
  if (Notification.permission === "default") {
    Notification.requestPermission();
  }
}
const css$1 = {
  code: ".notification-center.svelte-16e2to8.svelte-16e2to8{position:relative}.notification-bell.svelte-16e2to8.svelte-16e2to8{position:relative;background:none;border:none;padding:0.5rem;cursor:pointer;color:#666;transition:color 0.2s;border-radius:50%}.notification-bell.svelte-16e2to8.svelte-16e2to8:hover{color:#333;background:#f3f4f6}.notification-bell.has-unread.svelte-16e2to8.svelte-16e2to8{color:#3b82f6}.badge.svelte-16e2to8.svelte-16e2to8{position:absolute;top:0;right:0;background:#ef4444;color:white;font-size:0.7rem;font-weight:600;padding:0.125rem 0.375rem;border-radius:10px;min-width:18px;text-align:center}.notification-dropdown.svelte-16e2to8.svelte-16e2to8{position:absolute;top:100%;right:0;margin-top:0.5rem;width:380px;max-width:90vw;background:white;border-radius:12px;box-shadow:0 10px 40px rgba(0, 0, 0, 0.15);z-index:1000;overflow:hidden}.dropdown-header.svelte-16e2to8.svelte-16e2to8{display:flex;justify-content:space-between;align-items:center;padding:1rem 1.5rem;border-bottom:1px solid #e5e7eb}.dropdown-header.svelte-16e2to8 h3.svelte-16e2to8{margin:0;font-size:1.125rem;color:#111827}.clear-all.svelte-16e2to8.svelte-16e2to8{background:none;border:none;color:#6b7280;font-size:0.875rem;cursor:pointer;transition:color 0.2s}.clear-all.svelte-16e2to8.svelte-16e2to8:hover{color:#3b82f6}.notification-list.svelte-16e2to8.svelte-16e2to8{max-height:400px;overflow-y:auto}.empty-state.svelte-16e2to8.svelte-16e2to8{display:flex;flex-direction:column;align-items:center;gap:0.5rem;padding:3rem 1.5rem;color:#9ca3af}.empty-state.svelte-16e2to8 p.svelte-16e2to8{margin:0;font-size:0.875rem}.notification-item.svelte-16e2to8.svelte-16e2to8{display:flex;gap:1rem;padding:1rem 1.5rem;border-bottom:1px solid #f3f4f6;cursor:pointer;transition:background-color 0.2s;position:relative;width:100%;background:transparent;border:none;text-align:left;font-family:inherit}.notification-item.svelte-16e2to8.svelte-16e2to8:hover{background:#f9fafb}.notification-item.unread.svelte-16e2to8.svelte-16e2to8{background:#f0f9ff}.notification-item.unread.svelte-16e2to8.svelte-16e2to8::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:#3b82f6}.notification-icon.svelte-16e2to8.svelte-16e2to8{flex-shrink:0;display:flex;align-items:center;justify-content:center;width:40px;height:40px;background:#f3f4f6;border-radius:50%}.notification-content.svelte-16e2to8.svelte-16e2to8{flex:1;min-width:0}.notification-content.svelte-16e2to8 h4.svelte-16e2to8{margin:0 0 0.25rem 0;font-size:0.875rem;font-weight:600;color:#111827}.notification-content.svelte-16e2to8 p.svelte-16e2to8{margin:0 0 0.25rem 0;font-size:0.875rem;color:#6b7280;line-height:1.4}.timestamp.svelte-16e2to8.svelte-16e2to8{font-size:0.75rem;color:#9ca3af}.remove-btn.svelte-16e2to8.svelte-16e2to8{position:absolute;top:1rem;right:1rem;background:none;border:none;color:#9ca3af;cursor:pointer;padding:0.25rem;border-radius:4px;opacity:0;transition:all 0.2s}.notification-item.svelte-16e2to8:hover .remove-btn.svelte-16e2to8{opacity:1}.remove-btn.svelte-16e2to8.svelte-16e2to8:hover{background:#f3f4f6;color:#6b7280}@media(max-width: 640px){.notification-dropdown.svelte-16e2to8.svelte-16e2to8{position:fixed;top:auto;bottom:0;left:0;right:0;width:100%;max-width:100%;border-radius:12px 12px 0 0;max-height:70vh}.notification-list.svelte-16e2to8.svelte-16e2to8{max-height:calc(70vh - 60px)}}",
  map: `{"version":3,"file":"NotificationCenter.svelte","sources":["NotificationCenter.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { notifications, unreadCount } from \\"$lib/stores/notifications\\";\\nimport { Bell, X, CheckCircle, AlertCircle, AlertTriangle, Info } from \\"lucide-svelte\\";\\nimport { fly, fade } from \\"svelte/transition\\";\\nlet showNotifications = false;\\nfunction getIcon(type) {\\n  switch (type) {\\n    case \\"success\\":\\n      return CheckCircle;\\n    case \\"error\\":\\n      return AlertCircle;\\n    case \\"warning\\":\\n      return AlertTriangle;\\n    default:\\n      return Info;\\n  }\\n}\\nfunction getIconColor(type) {\\n  switch (type) {\\n    case \\"success\\":\\n      return \\"#10b981\\";\\n    case \\"error\\":\\n      return \\"#ef4444\\";\\n    case \\"warning\\":\\n      return \\"#f59e0b\\";\\n    default:\\n      return \\"#3b82f6\\";\\n  }\\n}\\nfunction handleNotificationClick(id) {\\n  notifications.markAsRead(id);\\n}\\nfunction handleRemove(id) {\\n  notifications.removeNotification(id);\\n}\\nfunction handleClearAll() {\\n  notifications.clearAll();\\n  showNotifications = false;\\n}\\nfunction handleClickOutside(event) {\\n  const target = event.target;\\n  if (!target.closest(\\".notification-center\\")) {\\n    showNotifications = false;\\n  }\\n}\\n<\/script>\\n\\n<svelte:window on:click={handleClickOutside} />\\n\\n<div class=\\"notification-center\\">\\n\\t<button \\n\\t\\tclass=\\"notification-bell\\"\\n\\t\\tclass:has-unread={$unreadCount > 0}\\n\\t\\ton:click|stopPropagation={() => showNotifications = !showNotifications}\\n\\t\\taria-label=\\"Notifications {$unreadCount > 0 ? \`(\${$unreadCount} unread)\` : ''}\\"\\n\\t\\taria-expanded={showNotifications}\\n\\t\\taria-haspopup=\\"true\\"\\n\\t>\\n\\t\\t<Bell size={20} />\\n\\t\\t{#if $unreadCount > 0}\\n\\t\\t\\t<span class=\\"badge\\">{$unreadCount}</span>\\n\\t\\t{/if}\\n\\t</button>\\n\\t\\n\\t{#if showNotifications}\\n\\t\\t<div \\n\\t\\t\\tclass=\\"notification-dropdown\\"\\n\\t\\t\\ttransition:fly={{ y: -10, duration: 200 }}\\n\\t\\t\\ton:click|stopPropagation\\n\\t\\t>\\n\\t\\t\\t<div class=\\"dropdown-header\\">\\n\\t\\t\\t\\t<h3>Notifications</h3>\\n\\t\\t\\t\\t{#if $notifications.length > 0}\\n\\t\\t\\t\\t\\t<button class=\\"clear-all\\" on:click={handleClearAll}>\\n\\t\\t\\t\\t\\t\\tClear all\\n\\t\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t</div>\\n\\t\\t\\t\\n\\t\\t\\t<div class=\\"notification-list\\">\\n\\t\\t\\t\\t{#if $notifications.length === 0}\\n\\t\\t\\t\\t\\t<div class=\\"empty-state\\">\\n\\t\\t\\t\\t\\t\\t<Bell size={32} />\\n\\t\\t\\t\\t\\t\\t<p>No notifications</p>\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t{#each $notifications as notification (notification.id)}\\n\\t\\t\\t\\t\\t\\t<button \\n\\t\\t\\t\\t\\t\\t\\tclass=\\"notification-item\\"\\n\\t\\t\\t\\t\\t\\t\\tclass:unread={!notification.read}\\n\\t\\t\\t\\t\\t\\t\\ton:click={() => handleNotificationClick(notification.id)}\\n\\t\\t\\t\\t\\t\\t\\ttransition:fade={{ duration: 200 }}\\n\\t\\t\\t\\t\\t\\t\\taria-label=\\"Mark notification as read\\"\\n\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t\\t\\t<div class=\\"notification-icon\\">\\n\\t\\t\\t\\t\\t\\t\\t\\t<svelte:component \\n\\t\\t\\t\\t\\t\\t\\t\\t\\tthis={getIcon(notification.type)} \\n\\t\\t\\t\\t\\t\\t\\t\\t\\tsize={20} \\n\\t\\t\\t\\t\\t\\t\\t\\t\\tcolor={getIconColor(notification.type)}\\n\\t\\t\\t\\t\\t\\t\\t\\t/>\\n\\t\\t\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\t\\t\\t<div class=\\"notification-content\\">\\n\\t\\t\\t\\t\\t\\t\\t\\t<h4>{notification.title}</h4>\\n\\t\\t\\t\\t\\t\\t\\t\\t<p>{notification.message}</p>\\n\\t\\t\\t\\t\\t\\t\\t\\t<span class=\\"timestamp\\">\\n\\t\\t\\t\\t\\t\\t\\t\\t\\t{notification.timestamp.toLocaleTimeString()}\\n\\t\\t\\t\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\t\\t\\t<button \\n\\t\\t\\t\\t\\t\\t\\t\\tclass=\\"remove-btn\\"\\n\\t\\t\\t\\t\\t\\t\\t\\ton:click|stopPropagation={() => handleRemove(notification.id)}\\n\\t\\t\\t\\t\\t\\t\\t\\taria-label=\\"Remove notification\\"\\n\\t\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t\\t\\t\\t<X size={16} />\\n\\t\\t\\t\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t\\t{/each}\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t{/if}\\n</div>\\n\\n<style>\\n\\t.notification-center {\\n\\t\\tposition: relative;\\n\\t}\\n\\t\\n\\t.notification-bell {\\n\\t\\tposition: relative;\\n\\t\\tbackground: none;\\n\\t\\tborder: none;\\n\\t\\tpadding: 0.5rem;\\n\\t\\tcursor: pointer;\\n\\t\\tcolor: #666;\\n\\t\\ttransition: color 0.2s;\\n\\t\\tborder-radius: 50%;\\n\\t}\\n\\t\\n\\t.notification-bell:hover {\\n\\t\\tcolor: #333;\\n\\t\\tbackground: #f3f4f6;\\n\\t}\\n\\t\\n\\t.notification-bell.has-unread {\\n\\t\\tcolor: #3b82f6;\\n\\t}\\n\\t\\n\\t.badge {\\n\\t\\tposition: absolute;\\n\\t\\ttop: 0;\\n\\t\\tright: 0;\\n\\t\\tbackground: #ef4444;\\n\\t\\tcolor: white;\\n\\t\\tfont-size: 0.7rem;\\n\\t\\tfont-weight: 600;\\n\\t\\tpadding: 0.125rem 0.375rem;\\n\\t\\tborder-radius: 10px;\\n\\t\\tmin-width: 18px;\\n\\t\\ttext-align: center;\\n\\t}\\n\\t\\n\\t.notification-dropdown {\\n\\t\\tposition: absolute;\\n\\t\\ttop: 100%;\\n\\t\\tright: 0;\\n\\t\\tmargin-top: 0.5rem;\\n\\t\\twidth: 380px;\\n\\t\\tmax-width: 90vw;\\n\\t\\tbackground: white;\\n\\t\\tborder-radius: 12px;\\n\\t\\tbox-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);\\n\\t\\tz-index: 1000;\\n\\t\\toverflow: hidden;\\n\\t}\\n\\t\\n\\t.dropdown-header {\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: space-between;\\n\\t\\talign-items: center;\\n\\t\\tpadding: 1rem 1.5rem;\\n\\t\\tborder-bottom: 1px solid #e5e7eb;\\n\\t}\\n\\t\\n\\t.dropdown-header h3 {\\n\\t\\tmargin: 0;\\n\\t\\tfont-size: 1.125rem;\\n\\t\\tcolor: #111827;\\n\\t}\\n\\t\\n\\t.clear-all {\\n\\t\\tbackground: none;\\n\\t\\tborder: none;\\n\\t\\tcolor: #6b7280;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: color 0.2s;\\n\\t}\\n\\t\\n\\t.clear-all:hover {\\n\\t\\tcolor: #3b82f6;\\n\\t}\\n\\t\\n\\t.notification-list {\\n\\t\\tmax-height: 400px;\\n\\t\\toverflow-y: auto;\\n\\t}\\n\\t\\n\\t.empty-state {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\talign-items: center;\\n\\t\\tgap: 0.5rem;\\n\\t\\tpadding: 3rem 1.5rem;\\n\\t\\tcolor: #9ca3af;\\n\\t}\\n\\t\\n\\t.empty-state p {\\n\\t\\tmargin: 0;\\n\\t\\tfont-size: 0.875rem;\\n\\t}\\n\\t\\n\\t.notification-item {\\n\\t\\tdisplay: flex;\\n\\t\\tgap: 1rem;\\n\\t\\tpadding: 1rem 1.5rem;\\n\\t\\tborder-bottom: 1px solid #f3f4f6;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: background-color 0.2s;\\n\\t\\tposition: relative;\\n\\t\\twidth: 100%;\\n\\t\\tbackground: transparent;\\n\\t\\tborder: none;\\n\\t\\ttext-align: left;\\n\\t\\tfont-family: inherit;\\n\\t}\\n\\t\\n\\t.notification-item:hover {\\n\\t\\tbackground: #f9fafb;\\n\\t}\\n\\t\\n\\t.notification-item.unread {\\n\\t\\tbackground: #f0f9ff;\\n\\t}\\n\\t\\n\\t.notification-item.unread::before {\\n\\t\\tcontent: '';\\n\\t\\tposition: absolute;\\n\\t\\tleft: 0;\\n\\t\\ttop: 0;\\n\\t\\tbottom: 0;\\n\\t\\twidth: 3px;\\n\\t\\tbackground: #3b82f6;\\n\\t}\\n\\t\\n\\t.notification-icon {\\n\\t\\tflex-shrink: 0;\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tjustify-content: center;\\n\\t\\twidth: 40px;\\n\\t\\theight: 40px;\\n\\t\\tbackground: #f3f4f6;\\n\\t\\tborder-radius: 50%;\\n\\t}\\n\\t\\n\\t.notification-content {\\n\\t\\tflex: 1;\\n\\t\\tmin-width: 0;\\n\\t}\\n\\t\\n\\t.notification-content h4 {\\n\\t\\tmargin: 0 0 0.25rem 0;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tfont-weight: 600;\\n\\t\\tcolor: #111827;\\n\\t}\\n\\t\\n\\t.notification-content p {\\n\\t\\tmargin: 0 0 0.25rem 0;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcolor: #6b7280;\\n\\t\\tline-height: 1.4;\\n\\t}\\n\\t\\n\\t.timestamp {\\n\\t\\tfont-size: 0.75rem;\\n\\t\\tcolor: #9ca3af;\\n\\t}\\n\\t\\n\\t.remove-btn {\\n\\t\\tposition: absolute;\\n\\t\\ttop: 1rem;\\n\\t\\tright: 1rem;\\n\\t\\tbackground: none;\\n\\t\\tborder: none;\\n\\t\\tcolor: #9ca3af;\\n\\t\\tcursor: pointer;\\n\\t\\tpadding: 0.25rem;\\n\\t\\tborder-radius: 4px;\\n\\t\\topacity: 0;\\n\\t\\ttransition: all 0.2s;\\n\\t}\\n\\t\\n\\t.notification-item:hover .remove-btn {\\n\\t\\topacity: 1;\\n\\t}\\n\\t\\n\\t.remove-btn:hover {\\n\\t\\tbackground: #f3f4f6;\\n\\t\\tcolor: #6b7280;\\n\\t}\\n\\t\\n\\t@media (max-width: 640px) {\\n\\t\\t.notification-dropdown {\\n\\t\\t\\tposition: fixed;\\n\\t\\t\\ttop: auto;\\n\\t\\t\\tbottom: 0;\\n\\t\\t\\tleft: 0;\\n\\t\\t\\tright: 0;\\n\\t\\t\\twidth: 100%;\\n\\t\\t\\tmax-width: 100%;\\n\\t\\t\\tborder-radius: 12px 12px 0 0;\\n\\t\\t\\tmax-height: 70vh;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.notification-list {\\n\\t\\t\\tmax-height: calc(70vh - 60px);\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"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"}`
};
const NotificationCenter = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $unreadCount, $$unsubscribe_unreadCount;
  let $$unsubscribe_notifications;
  $$unsubscribe_unreadCount = subscribe(unreadCount, (value) => $unreadCount = value);
  $$unsubscribe_notifications = subscribe(notifications, (value) => value);
  let showNotifications = false;
  $$result.css.add(css$1);
  $$unsubscribe_unreadCount();
  $$unsubscribe_notifications();
  return ` <div class="notification-center svelte-16e2to8"><button class="${["notification-bell svelte-16e2to8", $unreadCount > 0 ? "has-unread" : ""].join(" ").trim()}" aria-label="${"Notifications " + escape($unreadCount > 0 ? `(${$unreadCount} unread)` : "", true)}"${add_attribute("aria-expanded", showNotifications, 0)} aria-haspopup="true">${validate_component(Bell, "Bell").$$render($$result, { size: 20 }, {}, {})} ${$unreadCount > 0 ? `<span class="badge svelte-16e2to8">${escape($unreadCount)}</span>` : ``}</button> ${``} </div>`;
});
const css = {
  code: ".app.svelte-l103s9.svelte-l103s9{display:flex;flex-direction:column;min-height:100vh}header.svelte-l103s9.svelte-l103s9{background:#1a1a1a;color:white;padding:1rem 0;box-shadow:0 2px 4px rgba(0,0,0,0.1)}nav.svelte-l103s9.svelte-l103s9{max-width:1200px;margin:0 auto;padding:0 2rem;display:flex;justify-content:space-between;align-items:center}.logo.svelte-l103s9.svelte-l103s9{font-size:1.5rem;font-weight:bold;color:white;text-decoration:none}.nav-links.svelte-l103s9.svelte-l103s9{display:flex;gap:2rem;align-items:center}.nav-links.svelte-l103s9 a.svelte-l103s9{color:white;text-decoration:none;transition:opacity 0.2s}.nav-links.svelte-l103s9 a.svelte-l103s9:hover{opacity:0.8}main.svelte-l103s9.svelte-l103s9{flex:1;background:#f5f5f5;padding:2rem;max-width:1200px;margin:0 auto;width:100%;box-sizing:border-box}.nav-divider.svelte-l103s9.svelte-l103s9{width:1px;height:20px;background:rgba(255, 255, 255, 0.3);margin:0 1rem}.username.svelte-l103s9.svelte-l103s9{color:rgba(255, 255, 255, 0.9);font-weight:500}.logout-button.svelte-l103s9.svelte-l103s9{background:transparent;border:1px solid rgba(255, 255, 255, 0.3);color:white;padding:0.5rem 1rem;border-radius:6px;font-size:0.875rem;cursor:pointer;transition:all 0.2s}.logout-button.svelte-l103s9.svelte-l103s9:hover{background:rgba(255, 255, 255, 0.1);border-color:rgba(255, 255, 255, 0.5)}.register-button.svelte-l103s9.svelte-l103s9{background:#10b981;padding:0.5rem 1rem;border-radius:6px;transition:background 0.2s}.register-button.svelte-l103s9.svelte-l103s9:hover{background:#059669}@media(max-width: 768px){header.svelte-l103s9.svelte-l103s9{display:none}main.svelte-l103s9.svelte-l103s9{padding:1rem;padding-bottom:80px}}",
  map: `{"version":3,"file":"+layout.svelte","sources":["+layout.svelte"],"sourcesContent":["<script lang=\\"ts\\">import \\"./styles.css\\";\\nimport { auth, isAuthenticated } from \\"$lib/api/auth\\";\\nimport { goto } from \\"$app/navigation\\";\\nimport WebSocketStatus from \\"$lib/components/WebSocketStatus.svelte\\";\\nimport MobileNav from \\"$lib/components/MobileNav.svelte\\";\\nimport PWAInstallPrompt from \\"$lib/components/PWAInstallPrompt.svelte\\";\\nimport NotificationCenter from \\"$lib/components/NotificationCenter.svelte\\";\\nlet authState = { user: null, loading: true, error: null };\\nauth.subscribe((state) => {\\n  authState = state;\\n});\\nasync function handleLogout() {\\n  await auth.logout();\\n  goto(\\"/login\\");\\n}\\n<\/script>\\n\\n<div class=\\"app\\">\\n\\t<header>\\n\\t\\t<nav>\\n\\t\\t\\t<a href=\\"/\\" class=\\"logo\\">TradeSense</a>\\n\\t\\t\\t<div class=\\"nav-links\\">\\n\\t\\t\\t\\t{#if $isAuthenticated}\\n\\t\\t\\t\\t\\t<a href=\\"/\\">Dashboard</a>\\n\\t\\t\\t\\t\\t<a href=\\"/tradelog\\">Trade Log</a>\\n\\t\\t\\t\\t\\t<a href=\\"/journal\\">Journal</a>\\n\\t\\t\\t\\t\\t<a href=\\"/analytics\\">Analytics</a>\\n\\t\\t\\t\\t\\t<a href=\\"/playbook\\">Playbook</a>\\n\\t\\t\\t\\t\\t<div class=\\"nav-divider\\"></div>\\n\\t\\t\\t\\t\\t<WebSocketStatus />\\n\\t\\t\\t\\t\\t<NotificationCenter />\\n\\t\\t\\t\\t\\t<div class=\\"nav-divider\\"></div>\\n\\t\\t\\t\\t\\t<span class=\\"username\\">{authState?.user?.username || ''}</span>\\n\\t\\t\\t\\t\\t<button on:click={handleLogout} class=\\"logout-button\\">Logout</button>\\n\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t<a href=\\"/login\\">Login</a>\\n\\t\\t\\t\\t\\t<a href=\\"/register\\" class=\\"register-button\\">Sign Up</a>\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t</div>\\n\\t\\t</nav>\\n\\t</header>\\n\\n\\t<main>\\n\\t\\t<slot />\\n\\t</main>\\n\\t\\n\\t<MobileNav />\\n\\t<PWAInstallPrompt />\\n</div>\\n\\n<style>\\n\\t.app {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\tmin-height: 100vh;\\n\\t}\\n\\n\\theader {\\n\\t\\tbackground: #1a1a1a;\\n\\t\\tcolor: white;\\n\\t\\tpadding: 1rem 0;\\n\\t\\tbox-shadow: 0 2px 4px rgba(0,0,0,0.1);\\n\\t}\\n\\n\\tnav {\\n\\t\\tmax-width: 1200px;\\n\\t\\tmargin: 0 auto;\\n\\t\\tpadding: 0 2rem;\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: space-between;\\n\\t\\talign-items: center;\\n\\t}\\n\\n\\t.logo {\\n\\t\\tfont-size: 1.5rem;\\n\\t\\tfont-weight: bold;\\n\\t\\tcolor: white;\\n\\t\\ttext-decoration: none;\\n\\t}\\n\\n\\t.nav-links {\\n\\t\\tdisplay: flex;\\n\\t\\tgap: 2rem;\\n\\t\\talign-items: center;\\n\\t}\\n\\n\\t.nav-links a {\\n\\t\\tcolor: white;\\n\\t\\ttext-decoration: none;\\n\\t\\ttransition: opacity 0.2s;\\n\\t}\\n\\n\\t.nav-links a:hover {\\n\\t\\topacity: 0.8;\\n\\t}\\n\\n\\tmain {\\n\\t\\tflex: 1;\\n\\t\\tbackground: #f5f5f5;\\n\\t\\tpadding: 2rem;\\n\\t\\tmax-width: 1200px;\\n\\t\\tmargin: 0 auto;\\n\\t\\twidth: 100%;\\n\\t\\tbox-sizing: border-box;\\n\\t}\\n\\t\\n\\t.nav-divider {\\n\\t\\twidth: 1px;\\n\\t\\theight: 20px;\\n\\t\\tbackground: rgba(255, 255, 255, 0.3);\\n\\t\\tmargin: 0 1rem;\\n\\t}\\n\\t\\n\\t.username {\\n\\t\\tcolor: rgba(255, 255, 255, 0.9);\\n\\t\\tfont-weight: 500;\\n\\t}\\n\\t\\n\\t.logout-button {\\n\\t\\tbackground: transparent;\\n\\t\\tborder: 1px solid rgba(255, 255, 255, 0.3);\\n\\t\\tcolor: white;\\n\\t\\tpadding: 0.5rem 1rem;\\n\\t\\tborder-radius: 6px;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: all 0.2s;\\n\\t}\\n\\t\\n\\t.logout-button:hover {\\n\\t\\tbackground: rgba(255, 255, 255, 0.1);\\n\\t\\tborder-color: rgba(255, 255, 255, 0.5);\\n\\t}\\n\\t\\n\\t.register-button {\\n\\t\\tbackground: #10b981;\\n\\t\\tpadding: 0.5rem 1rem;\\n\\t\\tborder-radius: 6px;\\n\\t\\ttransition: background 0.2s;\\n\\t}\\n\\t\\n\\t.register-button:hover {\\n\\t\\tbackground: #059669;\\n\\t}\\n\\t\\n\\t/* Mobile Styles */\\n\\t@media (max-width: 768px) {\\n\\t\\theader {\\n\\t\\t\\tdisplay: none;\\n\\t\\t}\\n\\t\\t\\n\\t\\tmain {\\n\\t\\t\\tpadding: 1rem;\\n\\t\\t\\tpadding-bottom: 80px; /* Space for mobile nav */\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"AAmDC,gCAAK,CACJ,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,MAAM,CACtB,UAAU,CAAE,KACb,CAEA,kCAAO,CACN,UAAU,CAAE,OAAO,CACnB,KAAK,CAAE,KAAK,CACZ,OAAO,CAAE,IAAI,CAAC,CAAC,CACf,UAAU,CAAE,CAAC,CAAC,GAAG,CAAC,GAAG,CAAC,KAAK,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CACrC,CAEA,+BAAI,CACH,SAAS,CAAE,MAAM,CACjB,MAAM,CAAE,CAAC,CAAC,IAAI,CACd,OAAO,CAAE,CAAC,CAAC,IAAI,CACf,OAAO,CAAE,IAAI,CACb,eAAe,CAAE,aAAa,CAC9B,WAAW,CAAE,MACd,CAEA,iCAAM,CACL,SAAS,CAAE,MAAM,CACjB,WAAW,CAAE,IAAI,CACjB,KAAK,CAAE,KAAK,CACZ,eAAe,CAAE,IAClB,CAEA,sCAAW,CACV,OAAO,CAAE,IAAI,CACb,GAAG,CAAE,IAAI,CACT,WAAW,CAAE,MACd,CAEA,wBAAU,CAAC,eAAE,CACZ,KAAK,CAAE,KAAK,CACZ,eAAe,CAAE,IAAI,CACrB,UAAU,CAAE,OAAO,CAAC,IACrB,CAEA,wBAAU,CAAC,eAAC,MAAO,CAClB,OAAO,CAAE,GACV,CAEA,gCAAK,CACJ,IAAI,CAAE,CAAC,CACP,UAAU,CAAE,OAAO,CACnB,OAAO,CAAE,IAAI,CACb,SAAS,CAAE,MAAM,CACjB,MAAM,CAAE,CAAC,CAAC,IAAI,CACd,KAAK,CAAE,IAAI,CACX,UAAU,CAAE,UACb,CAEA,wCAAa,CACZ,KAAK,CAAE,GAAG,CACV,MAAM,CAAE,IAAI,CACZ,UAAU,CAAE,KAAK,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CACpC,MAAM,CAAE,CAAC,CAAC,IACX,CAEA,qCAAU,CACT,KAAK,CAAE,KAAK,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAC/B,WAAW,CAAE,GACd,CAEA,0CAAe,CACd,UAAU,CAAE,WAAW,CACvB,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,KAAK,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAC1C,KAAK,CAAE,KAAK,CACZ,OAAO,CAAE,MAAM,CAAC,IAAI,CACpB,aAAa,CAAE,GAAG,CAClB,SAAS,CAAE,QAAQ,CACnB,MAAM,CAAE,OAAO,CACf,UAAU,CAAE,GAAG,CAAC,IACjB,CAEA,0CAAc,MAAO,CACpB,UAAU,CAAE,KAAK,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CACpC,YAAY,CAAE,KAAK,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CAAC,CAAC,GAAG,CACtC,CAEA,4CAAiB,CAChB,UAAU,CAAE,OAAO,CACnB,OAAO,CAAE,MAAM,CAAC,IAAI,CACpB,aAAa,CAAE,GAAG,CAClB,UAAU,CAAE,UAAU,CAAC,IACxB,CAEA,4CAAgB,MAAO,CACtB,UAAU,CAAE,OACb,CAGA,MAAO,YAAY,KAAK,CAAE,CACzB,kCAAO,CACN,OAAO,CAAE,IACV,CAEA,gCAAK,CACJ,OAAO,CAAE,IAAI,CACb,cAAc,CAAE,IACjB,CACD"}`
};
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $isAuthenticated, $$unsubscribe_isAuthenticated;
  $$unsubscribe_isAuthenticated = subscribe(isAuthenticated, (value) => $isAuthenticated = value);
  let authState = { user: null };
  auth.subscribe((state) => {
    authState = state;
  });
  $$result.css.add(css);
  $$unsubscribe_isAuthenticated();
  return `<div class="app svelte-l103s9"><header class="svelte-l103s9"><nav class="svelte-l103s9"><a href="/" class="logo svelte-l103s9" data-svelte-h="svelte-cco7xr">TradeSense</a> <div class="nav-links svelte-l103s9">${$isAuthenticated ? `<a href="/" class="svelte-l103s9" data-svelte-h="svelte-505wu1">Dashboard</a> <a href="/tradelog" class="svelte-l103s9" data-svelte-h="svelte-1e6g5hd">Trade Log</a> <a href="/journal" class="svelte-l103s9" data-svelte-h="svelte-10k9vs1">Journal</a> <a href="/analytics" class="svelte-l103s9" data-svelte-h="svelte-46d8uv">Analytics</a> <a href="/playbook" class="svelte-l103s9" data-svelte-h="svelte-jmocgf">Playbook</a> <div class="nav-divider svelte-l103s9"></div> ${validate_component(WebSocketStatus, "WebSocketStatus").$$render($$result, {}, {}, {})} ${validate_component(NotificationCenter, "NotificationCenter").$$render($$result, {}, {}, {})} <div class="nav-divider svelte-l103s9"></div> <span class="username svelte-l103s9">${escape(authState?.user?.username || "")}</span> <button class="logout-button svelte-l103s9" data-svelte-h="svelte-81c2f8">Logout</button>` : `<a href="/login" class="svelte-l103s9" data-svelte-h="svelte-1vxwqu1">Login</a> <a href="/register" class="register-button svelte-l103s9" data-svelte-h="svelte-18wagad">Sign Up</a>`}</div></nav></header> <main class="svelte-l103s9">${slots.default ? slots.default({}) : ``}</main> ${validate_component(MobileNav, "MobileNav").$$render($$result, {}, {}, {})} ${validate_component(PWAInstallPrompt, "PWAInstallPrompt").$$render($$result, {}, {}, {})} </div>`;
});
export {
  Layout as default
};
