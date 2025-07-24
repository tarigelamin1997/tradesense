import "@sveltejs/kit/internal";
import "./exports.js";
import "./state.svelte.js";
function goto(url, opts = {}) {
  {
    throw new Error("Cannot call goto(...) on the server");
  }
}
export {
  goto as g
};
