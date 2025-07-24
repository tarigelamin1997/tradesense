import { A as AuthService } from "./auth.js";
const handle = async ({ event, resolve }) => {
  console.log(`[${(/* @__PURE__ */ new Date()).toISOString()}] Handling request: ${event.request.method} ${event.url.pathname}`);
  const token = AuthService.getAuthToken(event.cookies);
  const user = AuthService.getUser(event.cookies);
  event.locals.authToken = token;
  event.locals.user = user;
  event.locals.isAuthenticated = !!token && !!user;
  try {
    if (event.url.pathname === "/" || event.url.pathname.startsWith("/api")) {
      console.log("Environment check:", {
        NODE_ENV: process.env.NODE_ENV,
        VITE_API_URL_EXISTS: !!process.env.VITE_API_URL,
        PUBLIC_API_URL_EXISTS: !!process.env.PUBLIC_API_URL,
        DEPLOYMENT_URL: process.env.VERCEL_URL || "not-on-vercel"
      });
    }
    const response = await resolve(event);
    return response;
  } catch (error) {
    console.error(`[${(/* @__PURE__ */ new Date()).toISOString()}] Request error:`, error);
    throw error;
  }
};
const handleError = ({ error, event }) => {
  const timestamp = (/* @__PURE__ */ new Date()).toISOString();
  const errorId = Math.random().toString(36).substring(7);
  console.error(`[${timestamp}] Error ID: ${errorId}`);
  console.error("Request details:", {
    url: event.url.pathname,
    method: event.request.method,
    headers: Object.fromEntries(event.request.headers.entries()),
    platform: event.platform
  });
  if (error instanceof Error) {
    console.error("Error details:", {
      name: error.name,
      message: error.message,
      stack: error.stack,
      cause: error.cause
    });
  } else {
    console.error("Non-Error thrown:", error);
  }
  const errorMessage = error instanceof Error ? error.message : "Unknown error";
  error instanceof Error ? error.stack : "";
  if (errorMessage.includes("window is not defined") || errorMessage.includes("document is not defined") || errorMessage.includes("navigator is not defined") || errorMessage.includes("localStorage is not defined")) {
    return {
      message: "Server-side rendering error: Browser API accessed during SSR",
      code: "SSR_BROWSER_API"
    };
  }
  if (errorMessage.includes("Cannot read properties of null") || errorMessage.includes("Cannot read properties of undefined")) {
    return {
      message: "Server-side rendering error: Null reference during SSR",
      code: "SSR_NULL_REF"
    };
  }
  if (errorMessage.includes("Cannot find module") || errorMessage.includes("Module not found")) {
    return {
      message: `Module import error: ${errorMessage}`,
      code: "MODULE_NOT_FOUND"
    };
  }
  if (event.url.pathname.startsWith("/api/")) {
    console.error("API route error:", errorMessage);
  }
  const isDev = process.env.NODE_ENV === "development";
  return {
    message: isDev ? errorMessage : "An unexpected error occurred",
    code: "INTERNAL_ERROR",
    errorId
    // Include error ID for tracking
  };
};
export {
  handle,
  handleError
};
