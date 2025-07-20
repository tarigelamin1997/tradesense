import "./client.js";
import { d as derived, w as writable } from "./index.js";
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
function createAuthStore() {
  const { subscribe, set, update } = writable({
    user: null,
    loading: false,
    // Set to false by default for SSR
    error: null
  });
  return {
    subscribe,
    async login(credentials) {
      update((state) => ({ ...state, loading: true, error: null }));
      try {
        const response = await api.post("/api/v1/auth/login", {
          username: credentials.username,
          password: credentials.password
        });
        console.log("Login response:", response);
        if (response.access_token) {
          api.setAuthToken(response.access_token);
          const userInfo = await api.get("/api/v1/auth/me");
          update((state) => ({
            ...state,
            user: userInfo,
            loading: false,
            error: null
          }));
          return { access_token: response.access_token, token_type: "bearer", user: userInfo };
        }
        throw new Error("No access token received");
      } catch (error) {
        update((state) => ({
          ...state,
          user: null,
          loading: false,
          error: error.message || "Login failed"
        }));
        throw error;
      }
    },
    async register(data) {
      update((state) => ({ ...state, loading: true, error: null }));
      try {
        console.log("Attempting to register with:", data);
        const registerResponse = await api.post("/api/v1/auth/register", data);
        console.log("Registration successful:", registerResponse);
        const loginResponse = await this.login({
          username: data.username,
          password: data.password
        });
        return loginResponse;
      } catch (error) {
        console.error("Registration error:", error);
        let errorMessage = "Registration failed";
        if (error.detail?.details?.message) {
          errorMessage = error.detail.details.message;
        } else if (error.message) {
          errorMessage = error.message;
        }
        update((state) => ({
          ...state,
          user: null,
          loading: false,
          error: errorMessage
        }));
        throw error;
      }
    },
    async logout() {
      set({ user: null, loading: false, error: null });
    },
    async checkAuth() {
      {
        set({ user: null, loading: false, error: null });
        return;
      }
    },
    clearError() {
      update((state) => ({ ...state, error: null }));
    }
  };
}
const auth = createAuthStore();
const isAuthenticated = derived(
  auth,
  ($auth) => !!$auth.user
);
export {
  auth as a,
  api as b,
  isAuthenticated as i
};
