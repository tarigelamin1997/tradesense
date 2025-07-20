import { c as create_ssr_component, v as validate_component } from "./ssr.js";
import { I as Icon } from "./Icon2.js";
const Loader_circle = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M21 12a9 9 0 1 1-6.219-8.56" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "loader-circle" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
export {
  Loader_circle as L
};
