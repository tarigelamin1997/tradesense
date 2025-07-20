import { json } from "@sveltejs/kit";
const GET = async () => {
  const debugInfo = {
    timestamp: (/* @__PURE__ */ new Date()).toISOString(),
    environment: {
      NODE_ENV: process.env.NODE_ENV,
      VERCEL: process.env.VERCEL,
      VERCEL_ENV: process.env.VERCEL_ENV,
      VERCEL_URL: process.env.VERCEL_URL,
      VITE_API_URL: process.env.VITE_API_URL,
      PUBLIC_API_URL: process.env.PUBLIC_API_URL
    },
    runtime: {
      node_version: process.version,
      platform: process.platform,
      memory: process.memoryUsage()
    },
    message: "Debug endpoint working"
  };
  return json(debugInfo);
};
export {
  GET
};
