import { c as create_ssr_component, v as validate_component } from "./ssr.js";
import { I as Icon } from "./Icon2.js";
const Bug = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["path", { "d": "m8 2 1.88 1.88" }],
    ["path", { "d": "M14.12 3.88 16 2" }],
    [
      "path",
      {
        "d": "M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"
      }
    ],
    [
      "path",
      {
        "d": "M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"
      }
    ],
    ["path", { "d": "M12 20v-9" }],
    ["path", { "d": "M6.53 9C4.6 8.8 3 7.1 3 5" }],
    ["path", { "d": "M6 13H2" }],
    ["path", { "d": "M3 21c0-2.1 1.7-3.9 3.8-4" }],
    ["path", { "d": "M20.97 5c0 2.1-1.6 3.8-3.5 4" }],
    ["path", { "d": "M22 13h-4" }],
    ["path", { "d": "M17.2 17c2.1.1 3.8 1.9 3.8 4" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "bug" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Git_commit_horizontal = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "3" }],
    [
      "line",
      {
        "x1": "3",
        "x2": "9",
        "y1": "12",
        "y2": "12"
      }
    ],
    [
      "line",
      {
        "x1": "15",
        "x2": "21",
        "y1": "12",
        "y2": "12"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "git-commit-horizontal" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Package = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"
      }
    ],
    ["path", { "d": "M12 22V12" }],
    ["polyline", { "points": "3.29 7 12 12 20.71 7" }],
    ["path", { "d": "m7.5 4.27 9 5.15" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "package" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
export {
  Bug as B,
  Git_commit_horizontal as G,
  Package as P
};
