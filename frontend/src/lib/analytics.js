/**
 * Frontend analytics tracking for TradeSense
 */

import { browser } from '$app/environment';
import { page } from '$app/stores';
import { get } from 'svelte/store';

class Analytics {
    constructor() {
        this.queue = [];
        this.sessionId = this.generateSessionId();
        this.apiEndpoint = '/api/v1/analytics/track';
        this.flushInterval = 5000; // 5 seconds
        this.batchSize = 10;
        
        if (browser) {
            this.startAutoFlush();
            this.setupPageTracking();
            this.setupErrorTracking();
            this.setupPerformanceTracking();
        }
    }
    
    /**
     * Track an event
     */
    async track(eventType, properties = {}) {
        if (!browser) return;
        
        const event = {
            event_type: eventType,
            properties: {
                ...properties,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                screen_resolution: `${window.screen.width}x${window.screen.height}`,
                viewport_size: `${window.innerWidth}x${window.innerHeight}`,
                referrer: document.referrer,
                page_title: document.title
            },
            page_url: window.location.href,
            referrer_url: document.referrer,
            session_id: this.sessionId
        };
        
        this.queue.push(event);
        
        // Flush if queue is full
        if (this.queue.length >= this.batchSize) {
            await this.flush();
        }
    }
    
    /**
     * Track page view
     */
    trackPageView(url, properties = {}) {
        this.track('page_view', {
            url,
            ...properties
        });
    }
    
    /**
     * Track user action
     */
    trackAction(action, category, properties = {}) {
        this.track('user_action', {
            action,
            category,
            ...properties
        });
    }
    
    /**
     * Track feature usage
     */
    trackFeature(featureName, properties = {}) {
        this.track('feature_discovered', {
            feature_name: featureName,
            ...properties
        });
    }
    
    /**
     * Track error
     */
    trackError(error, properties = {}) {
        this.track('error_occurred', {
            error_message: error.message || String(error),
            error_stack: error.stack,
            ...properties
        });
    }
    
    /**
     * Track timing (performance)
     */
    trackTiming(category, variable, value, properties = {}) {
        this.track('timing', {
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
            create: 'trade_created',
            update: 'trade_updated',
            delete: 'trade_deleted',
            import: 'trade_imported'
        };
        
        this.track(eventTypeMap[action] || 'trade_created', {
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
            started: 'subscription_started',
            upgraded: 'subscription_upgraded',
            downgraded: 'subscription_downgraded',
            cancelled: 'subscription_cancelled'
        };
        
        this.track(eventTypeMap[action] || 'subscription_started', {
            plan,
            price,
            currency: 'USD'
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
            // Send events individually for now
            // In production, you might want to batch these
            for (const event of eventsToFlush) {
                await fetch(this.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.getAuthToken()}`
                    },
                    body: JSON.stringify(event)
                });
            }
        } catch (error) {
            console.error('Failed to send analytics:', error);
            // Re-queue events on failure
            this.queue = [...eventsToFlush, ...this.queue];
        }
    }
    
    /**
     * Set up automatic page tracking
     */
    setupPageTracking() {
        // Track initial page view
        this.trackPageView(window.location.href);
        
        // Subscribe to page changes
        page.subscribe(($page) => {
            if ($page.url) {
                this.trackPageView($page.url.href, {
                    route_id: $page.route.id,
                    params: $page.params
                });
            }
        });
        
        // Track time on page
        let startTime = Date.now();
        
        window.addEventListener('beforeunload', () => {
            const timeOnPage = Date.now() - startTime;
            this.track('page_exit', {
                time_on_page: timeOnPage,
                url: window.location.href
            });
            
            // Try to flush remaining events
            navigator.sendBeacon(this.apiEndpoint, JSON.stringify({
                events: this.queue
            }));
        });
    }
    
    /**
     * Set up error tracking
     */
    setupErrorTracking() {
        window.addEventListener('error', (event) => {
            this.trackError(event.error || event, {
                filename: event.filename,
                line_number: event.lineno,
                column_number: event.colno
            });
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.trackError(event.reason, {
                type: 'unhandled_promise_rejection'
            });
        });
    }
    
    /**
     * Set up performance tracking
     */
    setupPerformanceTracking() {
        // Track page load performance
        if (window.performance && window.performance.timing) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const timing = window.performance.timing;
                    const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
                    const domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
                    const firstPaintTime = this.getFirstPaintTime();
                    
                    this.track('page_performance', {
                        page_load_time: pageLoadTime,
                        dom_ready_time: domReadyTime,
                        first_paint_time: firstPaintTime,
                        url: window.location.href
                    });
                }, 0);
            });
        }
        
        // Track Web Vitals if available
        if ('PerformanceObserver' in window) {
            try {
                // Largest Contentful Paint
                const lcpObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    this.track('web_vital', {
                        metric: 'lcp',
                        value: lastEntry.startTime,
                        url: window.location.href
                    });
                });
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
                
                // First Input Delay
                const fidObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        this.track('web_vital', {
                            metric: 'fid',
                            value: entry.processingStart - entry.startTime,
                            url: window.location.href
                        });
                    });
                });
                fidObserver.observe({ entryTypes: ['first-input'] });
                
                // Cumulative Layout Shift
                let clsValue = 0;
                const clsObserver = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    entries.forEach((entry) => {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    });
                });
                clsObserver.observe({ entryTypes: ['layout-shift'] });
                
                // Report CLS on page unload
                window.addEventListener('beforeunload', () => {
                    this.track('web_vital', {
                        metric: 'cls',
                        value: clsValue,
                        url: window.location.href
                    });
                });
            } catch (error) {
                console.error('Failed to set up performance observers:', error);
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
        // This should get the actual auth token from your auth store
        return localStorage.getItem('auth_token') || '';
    }
    
    /**
     * Get first paint time
     */
    getFirstPaintTime() {
        if (window.performance && window.performance.getEntriesByType) {
            const paintEntries = window.performance.getEntriesByType('paint');
            const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
            return firstPaint ? firstPaint.startTime : null;
        }
        return null;
    }
    
    /**
     * Identify user (after login)
     */
    identify(userId, traits = {}) {
        this.track('user_identified', {
            user_id: userId,
            traits
        });
    }
    
    /**
     * Track form interactions
     */
    trackForm(formName, action, properties = {}) {
        this.track('form_interaction', {
            form_name: formName,
            action, // 'started', 'submitted', 'abandoned'
            ...properties
        });
    }
    
    /**
     * Track clicks
     */
    trackClick(element, properties = {}) {
        this.track('element_clicked', {
            element_text: element.textContent?.trim(),
            element_type: element.tagName?.toLowerCase(),
            element_class: element.className,
            element_id: element.id,
            ...properties
        });
    }
}

// Create singleton instance
const analytics = new Analytics();

// Export for use in components
export default analytics;

// Export convenience methods
export const {
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