import { c as create_ssr_component, v as validate_component } from "./ssr.js";
import { I as Icon } from "./Icon2.js";
const Brain = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"
      }
    ],
    [
      "path",
      {
        "d": "M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"
      }
    ],
    [
      "path",
      {
        "d": "M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"
      }
    ],
    ["path", { "d": "M17.599 6.5a3 3 0 0 0 .399-1.375" }],
    ["path", { "d": "M6.003 5.125A3 3 0 0 0 6.401 6.5" }],
    ["path", { "d": "M3.477 10.896a4 4 0 0 1 .585-.396" }],
    ["path", { "d": "M19.938 10.5a4 4 0 0 1 .585.396" }],
    ["path", { "d": "M6 18a4 4 0 0 1-1.967-.516" }],
    ["path", { "d": "M19.967 17.484A4 4 0 0 1 18 18" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "brain" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
export {
  Brain as B
};
