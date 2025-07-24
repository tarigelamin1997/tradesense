import { i as initI18n } from "../../chunks/index3.js";
import { w as waitLocale } from "../../chunks/runtime.js";
const load = async () => {
  await initI18n();
  await waitLocale();
  return {};
};
export {
  load
};
