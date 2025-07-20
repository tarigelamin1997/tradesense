import { c as create_ssr_component, v as validate_component } from "./ssr.js";
import { I as Icon } from "./Icon2.js";
const File_spreadsheet = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"
      }
    ],
    ["path", { "d": "M14 2v4a2 2 0 0 0 2 2h4" }],
    ["path", { "d": "M8 13h2" }],
    ["path", { "d": "M14 13h2" }],
    ["path", { "d": "M8 17h2" }],
    ["path", { "d": "M14 17h2" }]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "file-spreadsheet" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
export {
  File_spreadsheet as F
};
