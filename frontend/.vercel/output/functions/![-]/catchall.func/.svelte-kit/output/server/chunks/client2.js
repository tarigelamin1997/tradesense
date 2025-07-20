import axios from "axios";
import "./client.js";
const API_BASE_URL = "https://tradesense-gateway-production.up.railway.app";
class ApiClient {
  client;
  token = null;
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 3e4,
      headers: {
        "Content-Type": "application/json"
      }
    });
    this.setupInterceptors();
  }
  setupInterceptors() {
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        console.error("API Error:", {
          url: error.config?.url,
          method: error.config?.method,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        });
        if (error.response?.status === 401) {
          this.clearAuth();
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
  // Auth methods
  setAuthToken(token) {
    this.token = token;
  }
  clearAuth() {
    this.token = null;
  }
  isAuthenticated() {
    return !!this.token;
  }
  // API methods
  async get(url, params) {
    const response = await this.client.get(url, { params });
    return response.data;
  }
  async post(url, data, config) {
    const response = await this.client.post(url, data, config);
    return response.data;
  }
  async put(url, data) {
    const response = await this.client.put(url, data);
    return response.data;
  }
  async patch(url, data) {
    const response = await this.client.patch(url, data);
    return response.data;
  }
  async delete(url) {
    const response = await this.client.delete(url);
    return response.data;
  }
}
const api = new ApiClient();
export {
  api as a
};
