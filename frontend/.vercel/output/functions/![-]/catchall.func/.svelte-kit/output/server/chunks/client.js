import "@sveltejs/kit/internal";
import "./exports.js";
import "./state.svelte.js";
const api = {
  get: () => Promise.reject(new Error("API not available during SSR")),
  post: () => Promise.reject(new Error("API not available during SSR")),
  put: () => Promise.reject(new Error("API not available during SSR")),
  patch: () => Promise.reject(new Error("API not available during SSR")),
  delete: () => Promise.reject(new Error("API not available during SSR")),
  upload: () => Promise.reject(new Error("API not available during SSR"))
};
export {
  api as a
};
