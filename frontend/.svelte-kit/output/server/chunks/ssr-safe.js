import { b as browser } from "./index2.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./state.svelte.js";
class SSRSafeApiClient {
  static instance = null;
  axiosInstance = null;
  initialized = false;
  constructor() {
  }
  static getInstance() {
    if (!SSRSafeApiClient.instance) {
      SSRSafeApiClient.instance = new SSRSafeApiClient();
    }
    return SSRSafeApiClient.instance;
  }
  async initializeClient() {
    if (this.initialized || !browser) return;
  }
  setupInterceptors() {
    if (!this.axiosInstance) return;
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          this.clearStoredToken();
        }
        const responseData = error.response?.data;
        const apiError = {
          message: responseData?.detail || responseData?.message || error.message || "An error occurred",
          status: error.response?.status || 500,
          detail: responseData
        };
        return Promise.reject(apiError);
      }
    );
  }
  getStoredToken() {
    return null;
  }
  clearStoredToken() {
    return;
  }
  // Public API methods
  async get(url, params) {
    {
      return {};
    }
  }
  async post(url, data, config) {
    {
      return {};
    }
  }
  async put(url, data) {
    {
      return {};
    }
  }
  async patch(url, data) {
    {
      return {};
    }
  }
  async delete(url) {
    {
      return {};
    }
  }
  setAuthToken(token) {
    return;
  }
  clearAuth() {
    return;
  }
  getAuthToken() {
    return this.getStoredToken();
  }
  isAuthenticated() {
    return !!this.getStoredToken();
  }
}
const api = SSRSafeApiClient.getInstance();
export {
  api as a
};
