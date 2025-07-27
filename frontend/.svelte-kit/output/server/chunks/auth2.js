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
        const apiUrl2 = "http://localhost:8000";
        console.log("Attempting login to:", apiUrl2);
        console.log("Username:", credentials.username);
        const loginUrl = `${apiUrl2}/auth/token`;
        console.log("Login URL:", loginUrl);
        const response = await fetch(loginUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: formData.toString(),
          credentials: "include"
        });
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          console.error("Login failed:", response.status, response.statusText, errorData);
          throw new Error(errorData.detail || `Login failed: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        console.log("Login response:", data);
        if (data.access_token) {
          const userResponse = await fetch(`${apiUrl2}/auth/me`, {
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
        console.error("Error details:", {
          name: error.name,
          message: error.message,
          stack: error.stack
        });
        let errorMessage = "Login failed";
        if (error.name === "TypeError" && error.message.includes("Failed to fetch")) {
          errorMessage = `Unable to connect to server at ${apiUrl}. Please check if the backend is running and CORS is configured.`;
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
        const apiUrl2 = "http://localhost:8000";
        console.log("Attempting to register at:", apiUrl2);
        console.log("Registration data:", data);
        const registerUrl = `${apiUrl2}/auth/register`;
        console.log("Register URL:", registerUrl);
        const registerResponse = await fetch(registerUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify(data),
          credentials: "include"
        });
        if (!registerResponse.ok) {
          const errorData = await registerResponse.json().catch(() => ({}));
          console.error("Registration failed:", registerResponse.status, registerResponse.statusText, errorData);
          throw new Error(errorData.detail || `Registration failed: ${registerResponse.status} ${registerResponse.statusText}`);
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
        const apiUrl2 = "http://localhost:8000";
        await fetch(`${apiUrl2}/auth/logout`, {
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
