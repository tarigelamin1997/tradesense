import "./client.js";
async function getApiClient() {
  {
    return {
      get: () => Promise.reject(new Error("API not available during SSR")),
      post: () => Promise.reject(new Error("API not available during SSR")),
      put: () => Promise.reject(new Error("API not available during SSR")),
      patch: () => Promise.reject(new Error("API not available during SSR")),
      delete: () => Promise.reject(new Error("API not available during SSR"))
    };
  }
}
const api = {
  async get(url, params) {
    const client = await getApiClient();
    const response = await client.get(url, { params });
    return response.data;
  },
  async post(url, data, config) {
    const client = await getApiClient();
    const response = await client.post(url, data, config);
    return response.data;
  },
  async put(url, data) {
    const client = await getApiClient();
    const response = await client.put(url, data);
    return response.data;
  },
  async patch(url, data) {
    const client = await getApiClient();
    const response = await client.patch(url, data);
    return response.data;
  },
  async delete(url) {
    const client = await getApiClient();
    const response = await client.delete(url);
    return response.data;
  },
  setAuthToken(token) {
    return;
  },
  clearAuth() {
    return;
  },
  getAuthToken() {
    return null;
  },
  isAuthenticated() {
    return false;
  }
};
export {
  api as a
};
