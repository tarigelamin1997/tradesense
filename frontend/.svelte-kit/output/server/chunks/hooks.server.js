const handleError = ({ error, event }) => {
  console.error("Server error:", error);
  console.error("Request URL:", event.url.pathname);
  console.error("Request method:", event.request.method);
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
  if (event.url.pathname.startsWith("/api/")) {
    console.error("API route error:", errorMessage);
  }
  return {
    message: "An unexpected error occurred",
    code: "INTERNAL_ERROR"
  };
};
export {
  handleError
};
