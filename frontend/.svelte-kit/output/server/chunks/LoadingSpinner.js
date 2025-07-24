import { c as create_ssr_component, b as escape } from "./ssr.js";
const LoadingSpinner = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { size = "md" } = $$props;
  let { color = "primary" } = $$props;
  let { fullScreen = false } = $$props;
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-8 w-8",
    lg: "h-12 w-12",
    xl: "h-16 w-16"
  };
  const colorClasses = {
    primary: "text-blue-600",
    white: "text-white",
    gray: "text-gray-400"
  };
  if ($$props.size === void 0 && $$bindings.size && size !== void 0) $$bindings.size(size);
  if ($$props.color === void 0 && $$bindings.color && color !== void 0) $$bindings.color(color);
  if ($$props.fullScreen === void 0 && $$bindings.fullScreen && fullScreen !== void 0) $$bindings.fullScreen(fullScreen);
  return `${fullScreen ? `<div class="fixed inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-50 flex items-center justify-center"><div class="${"animate-spin " + escape(sizeClasses[size], true) + " " + escape(colorClasses[color], true)}"><svg class="w-full h-full" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div></div>` : `<div class="${"animate-spin " + escape(sizeClasses[size], true) + " " + escape(colorClasses[color], true)}"><svg class="w-full h-full" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg></div>`}`;
});
export {
  LoadingSpinner as L
};
