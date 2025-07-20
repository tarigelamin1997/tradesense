import { d as derived, w as writable } from "./index.js";
import "./client.js";
import { a as api } from "./client2.js";
function createAuthStore() {
  const { subscribe, set, update } = writable({
    user: null,
    token: null,
    loading: true,
    initialized: false
  });
  let refreshTimeout;
  async function initialize() {
    return;
  }
  async function login(email, password, mfaCode) {
    try {
      const response = await api.post("/api/v1/auth/login", {
        email,
        password,
        mfa_code: mfaCode
      });
      const { access_token, user: user2 } = response.data;
      localStorage.setItem("auth_token", access_token);
      localStorage.setItem("user", JSON.stringify(user2));
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
      update((state) => ({
        ...state,
        user: user2,
        token: access_token,
        loading: false
      }));
      scheduleTokenRefresh();
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || "Login failed";
      return {
        success: false,
        error: message,
        requiresMfa: error.response?.status === 428
      };
    }
  }
  async function register(email, password, name) {
    try {
      const response = await api.post("/api/v1/auth/register", {
        email,
        password,
        name
      });
      const { access_token, user: user2 } = response.data;
      localStorage.setItem("auth_token", access_token);
      localStorage.setItem("user", JSON.stringify(user2));
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
      update((state) => ({
        ...state,
        user: user2,
        token: access_token,
        loading: false
      }));
      scheduleTokenRefresh();
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || "Registration failed";
      return { success: false, error: message };
    }
  }
  async function logout() {
    try {
      await api.post("/api/v1/auth/logout");
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      delete api.defaults.headers.common["Authorization"];
      if (refreshTimeout) {
        clearTimeout(refreshTimeout);
      }
      set({
        user: null,
        token: null,
        loading: false,
        initialized: true
      });
    }
  }
  async function checkAuth() {
    try {
      const response = await api.get("/api/v1/auth/me");
      const user2 = response.data;
      localStorage.setItem("user", JSON.stringify(user2));
      update((state) => ({
        ...state,
        user: user2
      }));
      return true;
    } catch (error) {
      console.error("Auth check failed:", error);
      await logout();
      return false;
    }
  }
  async function refreshToken() {
    try {
      const response = await api.post("/api/v1/auth/refresh");
      const { access_token } = response.data;
      localStorage.setItem("auth_token", access_token);
      api.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
      update((state) => ({
        ...state,
        token: access_token
      }));
      scheduleTokenRefresh();
      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      await logout();
      return false;
    }
  }
  function scheduleTokenRefresh() {
    if (refreshTimeout) {
      clearTimeout(refreshTimeout);
    }
    refreshTimeout = setTimeout(() => {
      refreshToken();
    }, 25 * 60 * 1e3);
  }
  async function updateUser(updates) {
    try {
      const response = await api.patch("/api/v1/auth/me", updates);
      const user2 = response.data;
      localStorage.setItem("user", JSON.stringify(user2));
      update((state) => ({
        ...state,
        user: user2
      }));
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || "Update failed";
      return { success: false, error: message };
    }
  }
  return {
    subscribe,
    login,
    register,
    logout,
    checkAuth,
    refreshToken,
    updateUser,
    initialize
  };
}
const authStore = createAuthStore();
derived(authStore, ($authStore) => $authStore.user);
derived(authStore, ($authStore) => !!$authStore.user);
derived(authStore, ($authStore) => $authStore.user?.is_admin || false);
export {
  authStore as a
};
