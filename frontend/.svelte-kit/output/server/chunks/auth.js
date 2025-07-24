const AUTH_COOKIE_NAME = "tradesense_auth_token";
const USER_COOKIE_NAME = "tradesense_user";
const REFRESH_COOKIE_NAME = "tradesense_refresh_token";
const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: true,
  // Use secure cookies in production
  sameSite: "lax",
  path: "/",
  maxAge: 60 * 60 * 24 * 7
  // 7 days
};
const USER_COOKIE_OPTIONS = {
  httpOnly: false,
  // User data can be read by client
  secure: true,
  sameSite: "lax",
  path: "/",
  maxAge: 60 * 60 * 24 * 7
  // 7 days
};
class AuthService {
  /**
   * Set authentication cookies
   */
  static setAuthCookies(cookies, token, refreshToken, user) {
    cookies.set(AUTH_COOKIE_NAME, token, COOKIE_OPTIONS);
    cookies.set(REFRESH_COOKIE_NAME, refreshToken, {
      ...COOKIE_OPTIONS,
      maxAge: 60 * 60 * 24 * 30
      // 30 days for refresh token
    });
    cookies.set(USER_COOKIE_NAME, JSON.stringify(user), USER_COOKIE_OPTIONS);
  }
  /**
   * Get authentication token from cookies
   */
  static getAuthToken(cookies) {
    return cookies.get(AUTH_COOKIE_NAME) || null;
  }
  /**
   * Get refresh token from cookies
   */
  static getRefreshToken(cookies) {
    return cookies.get(REFRESH_COOKIE_NAME) || null;
  }
  /**
   * Get user data from cookies
   */
  static getUser(cookies) {
    const userCookie = cookies.get(USER_COOKIE_NAME);
    if (!userCookie) return null;
    try {
      return JSON.parse(userCookie);
    } catch {
      return null;
    }
  }
  /**
   * Clear all authentication cookies
   */
  static clearAuthCookies(cookies) {
    cookies.delete(AUTH_COOKIE_NAME, { path: "/" });
    cookies.delete(REFRESH_COOKIE_NAME, { path: "/" });
    cookies.delete(USER_COOKIE_NAME, { path: "/" });
  }
  /**
   * Validate token format (basic validation)
   */
  static isValidTokenFormat(token) {
    const parts = token.split(".");
    return parts.length === 3 && parts.every((part) => part.length > 0);
  }
  /**
   * Extract token expiry from JWT (without verification)
   */
  static getTokenExpiry(token) {
    try {
      const parts = token.split(".");
      if (parts.length !== 3) return null;
      const payload = JSON.parse(atob(parts[1]));
      if (!payload.exp) return null;
      return new Date(payload.exp * 1e3);
    } catch {
      return null;
    }
  }
  /**
   * Check if token is expired
   */
  static isTokenExpired(token) {
    const expiry = this.getTokenExpiry(token);
    if (!expiry) return true;
    return expiry < /* @__PURE__ */ new Date();
  }
}
export {
  AuthService as A
};
