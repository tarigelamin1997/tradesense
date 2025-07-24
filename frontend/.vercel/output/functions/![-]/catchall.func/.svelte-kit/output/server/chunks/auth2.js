import "@sveltejs/kit/internal";
import "./exports.js";
import { d as derived, w as writable } from "./index.js";
import "./state.svelte.js";
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
        const formData = new URLSearchParams();
        formData.append("username", credentials.username);
        formData.append("password", credentials.password);
        console.log("Attempting login with username:", credentials.username);
        const response = await fetch(`${"https://tradesense-backend-production.up.railway.app"}/auth/token`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: formData.toString(),
          credentials: "include"
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || "Login failed");
        }
        const data = await response.json();
        console.log("Login response:", data);
        if (data.access_token) {
          const userResponse = await fetch(`${"https://tradesense-backend-production.up.railway.app"}/auth/me`, {
            headers: {
              "Authorization": `Bearer ${data.access_token}`
            },
            credentials: "include"
          });
          if (!userResponse.ok) {
            throw new Error("Failed to get user info");
          }
          const userInfo = await userResponse.json();
          update((state) => ({
            ...state,
            user: userInfo,
            loading: false,
            error: null
          }));
          return {
            access_token: data.access_token,
            token_type: "bearer",
            user: userInfo,
            mfa_required: data.mfa_required,
            session_id: data.session_id,
            methods: data.methods
          };
        }
        throw new Error("No access token received");
      } catch (error) {
        console.error("Login error:", error);
        let errorMessage = "Login failed";
        if (error.message && error.message.includes("fetch")) {
          errorMessage = "Unable to connect to server. Please ensure the backend is running on port 8000.";
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
    async register(data) {
      update((state) => ({ ...state, loading: true, error: null }));
      try {
        console.log("Attempting to register with:", data);
        const registerResponse = await fetch(`${"https://tradesense-backend-production.up.railway.app"}/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(data),
          credentials: "include"
        });
        if (!registerResponse.ok) {
          const errorData = await registerResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || "Registration failed");
        }
        console.log("Registration successful");
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
        } else if (error.detail && typeof error.detail === "string") {
          errorMessage = error.detail;
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
      try {
        await fetch(`${"https://tradesense-backend-production.up.railway.app"}/auth/logout`, {
          method: "POST",
          credentials: "include"
        });
      } catch (error) {
        console.error("Logout error:", error);
      }
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
  isAuthenticated as i
};
