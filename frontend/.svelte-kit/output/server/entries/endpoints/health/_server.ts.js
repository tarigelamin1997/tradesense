import { json } from "@sveltejs/kit";
const GET = async () => {
  return json({
    status: "ok",
    timestamp: (/* @__PURE__ */ new Date()).toISOString(),
    message: "Frontend health check endpoint",
    environment: {
      NODE_ENV: process.env.NODE_ENV || "unknown",
      HAS_VITE_API_URL: !!process.env.VITE_API_URL
    }
  });
};
export {
  GET
};
