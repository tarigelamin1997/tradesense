import { p as page } from "./stores.js";
class Analytics {
  constructor() {
    this.queue = [];
    this.sessionId = this.generateSessionId();
    this.apiEndpoint = "/api/v1/analytics/track";
    this.flushInterval = 5e3;
    this.batchSize = 10;
  }
  /**
   * Track an event
   */
  async track(eventType, properties = {}) {
    return;
  }
  /**
   * Track page view
   */
  trackPageView(url, properties = {}) {
    this.track("page_view", {
      url,
      ...properties
    });
  }
  /**
   * Track user action
   */
  trackAction(action, category, properties = {}) {
    this.track("user_action", {
      action,
      category,
      ...properties
    });
  }
  /**
   * Track feature usage
   */
  trackFeature(featureName, properties = {}) {
    this.track("feature_discovered", {
      feature_name: featureName,
      ...properties
    });
  }
  /**
   * Track error
   */
  trackError(error, properties = {}) {
    this.track("error_occurred", {
      error_message: error.message || String(error),
      error_stack: error.stack,
      ...properties
    });
  }
  /**
   * Track timing (performance)
   */
  trackTiming(category, variable, value, properties = {}) {
    this.track("timing", {
      category,
      variable,
      value,
      ...properties
    });
  }
  /**
   * Track trade events
   */
  trackTrade(action, tradeData) {
    const eventTypeMap = {
      create: "trade_created",
      update: "trade_updated",
      delete: "trade_deleted",
      import: "trade_imported"
    };
    this.track(eventTypeMap[action] || "trade_created", {
      trade_id: tradeData.id,
      symbol: tradeData.symbol,
      trade_type: tradeData.trade_type,
      quantity: tradeData.quantity,
      value: tradeData.entry_price * tradeData.quantity,
      profit_loss: tradeData.profit_loss
    });
  }
  /**
   * Track subscription events
   */
  trackSubscription(action, plan, price) {
    const eventTypeMap = {
      started: "subscription_started",
      upgraded: "subscription_upgraded",
      downgraded: "subscription_downgraded",
      cancelled: "subscription_cancelled"
    };
    this.track(eventTypeMap[action] || "subscription_started", {
      plan,
      price,
      currency: "USD"
    });
  }
  /**
   * Flush events to server
   */
  async flush() {
    if (this.queue.length === 0) return;
    const eventsToFlush = [...this.queue];
    this.queue = [];
    try {
      for (const event of eventsToFlush) {
        await fetch(this.apiEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${this.getAuthToken()}`
          },
          body: JSON.stringify(event)
        });
      }
    } catch (error) {
      console.error("Failed to send analytics:", error);
      this.queue = [...eventsToFlush, ...this.queue];
    }
  }
  /**
   * Set up automatic page tracking
   */
  setupPageTracking() {
    this.trackPageView(window.location.href);
    page.subscribe(($page) => {
      if ($page.url) {
        this.trackPageView($page.url.href, {
          route_id: $page.route.id,
          params: $page.params
        });
      }
    });
    let startTime = Date.now();
    window.addEventListener("beforeunload", () => {
      const timeOnPage = Date.now() - startTime;
      this.track("page_exit", {
        time_on_page: timeOnPage,
        url: window.location.href
      });
      if (navigator?.sendBeacon) {
        navigator.sendBeacon(this.apiEndpoint, JSON.stringify({
          events: this.queue
        }));
      }
    });
  }
  /**
   * Set up error tracking
   */
  setupErrorTracking() {
    window.addEventListener("error", (event) => {
      this.trackError(event.error || event, {
        filename: event.filename,
        line_number: event.lineno,
        column_number: event.colno
      });
    });
    window.addEventListener("unhandledrejection", (event) => {
      this.trackError(event.reason, {
        type: "unhandled_promise_rejection"
      });
    });
  }
  /**
   * Set up performance tracking
   */
  setupPerformanceTracking() {
    if (window.performance && window.performance.timing) {
      window.addEventListener("load", () => {
        setTimeout(() => {
          const timing = window.performance.timing;
          const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
          const domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
          const firstPaintTime = this.getFirstPaintTime();
          this.track("page_performance", {
            page_load_time: pageLoadTime,
            dom_ready_time: domReadyTime,
            first_paint_time: firstPaintTime,
            url: window.location.href
          });
        }, 0);
      });
    }
    if ("PerformanceObserver" in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.track("web_vital", {
            metric: "lcp",
            value: lastEntry.startTime,
            url: window.location.href
          });
        });
        lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            this.track("web_vital", {
              metric: "fid",
              value: entry.processingStart - entry.startTime,
              url: window.location.href
            });
          });
        });
        fidObserver.observe({ entryTypes: ["first-input"] });
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
        });
        clsObserver.observe({ entryTypes: ["layout-shift"] });
        window.addEventListener("beforeunload", () => {
          this.track("web_vital", {
            metric: "cls",
            value: clsValue,
            url: window.location.href
          });
        });
      } catch (error) {
        console.error("Failed to set up performance observers:", error);
      }
    }
  }
  /**
   * Start auto-flush interval
   */
  startAutoFlush() {
    setInterval(() => {
      this.flush();
    }, this.flushInterval);
  }
  /**
   * Generate session ID
   */
  generateSessionId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  /**
   * Get auth token
   */
  getAuthToken() {
    return "";
  }
  /**
   * Get first paint time
   */
  getFirstPaintTime() {
    if (window.performance && window.performance.getEntriesByType) {
      const paintEntries = window.performance.getEntriesByType("paint");
      const firstPaint = paintEntries.find((entry) => entry.name === "first-paint");
      return firstPaint ? firstPaint.startTime : null;
    }
    return null;
  }
  /**
   * Identify user (after login)
   */
  identify(userId, traits = {}) {
    this.track("user_identified", {
      user_id: userId,
      traits
    });
  }
  /**
   * Track form interactions
   */
  trackForm(formName, action, properties = {}) {
    this.track("form_interaction", {
      form_name: formName,
      action,
      // 'started', 'submitted', 'abandoned'
      ...properties
    });
  }
  /**
   * Track clicks
   */
  trackClick(element, properties = {}) {
    this.track("element_clicked", {
      element_text: element.textContent?.trim(),
      element_type: element.tagName?.toLowerCase(),
      element_class: element.className,
      element_id: element.id,
      ...properties
    });
  }
}
const analytics = new Analytics();
const {
  track,
  trackPageView,
  trackAction,
  trackFeature,
  trackError,
  trackTiming,
  trackTrade,
  trackSubscription,
  identify,
  trackForm,
  trackClick
} = analytics;
export {
  analytics as a
};
