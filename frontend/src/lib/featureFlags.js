/**
 * Feature flags client for TradeSense frontend
 * Manages feature toggles and A/B testing
 */

import { api } from './api';
import { get, writable } from 'svelte/store';
import { browser } from '$app/environment';

class FeatureFlagsClient {
    constructor() {
        // Store for feature flag values
        this.flags = writable({});
        this.loading = writable(true);
        this.error = writable(null);
        
        // Cache settings
        this.cacheKey = 'tradesense_feature_flags';
        this.cacheTTL = 5 * 60 * 1000; // 5 minutes
        
        // Default flag values (fallbacks)
        this.defaults = {
            new_analytics_dashboard: false,
            ai_trade_insights: false,
            mobile_app_beta: false,
            export_format: 'csv',
            advanced_filtering: false,
            real_time_sync: false,
            collaborative_features: false
        };
    }
    
    /**
     * Initialize feature flags for user
     */
    async initialize() {
        try {
            this.loading.set(true);
            this.error.set(null);
            
            // Check cache first
            const cached = this.getCachedFlags();
            if (cached) {
                this.flags.set(cached);
                this.loading.set(false);
                
                // Refresh in background
                this.refreshFlags();
                return;
            }
            
            // Fetch from server
            await this.refreshFlags();
            
        } catch (err) {
            console.error('Failed to initialize feature flags:', err);
            this.error.set(err.message);
            
            // Use defaults on error
            this.flags.set(this.defaults);
        } finally {
            this.loading.set(false);
        }
    }
    
    /**
     * Refresh flags from server
     */
    async refreshFlags() {
        try {
            const response = await api.get('/feature-flags/evaluate');
            
            if (response && response.flags) {
                this.flags.set(response.flags);
                this.cacheFlags(response.flags);
            }
            
        } catch (err) {
            console.error('Failed to refresh feature flags:', err);
            // Don't update error state for background refresh
        }
    }
    
    /**
     * Get a specific flag value
     */
    getFlag(key, defaultValue = null) {
        const flags = get(this.flags);
        
        if (key in flags) {
            return flags[key];
        }
        
        if (key in this.defaults) {
            return this.defaults[key];
        }
        
        return defaultValue;
    }
    
    /**
     * Check if a feature is enabled
     */
    isEnabled(key) {
        return this.getFlag(key, false) === true;
    }
    
    /**
     * Get variant for A/B test
     */
    getVariant(key, defaultVariant = 'control') {
        const value = this.getFlag(key);
        return typeof value === 'string' ? value : defaultVariant;
    }
    
    /**
     * Track feature usage
     */
    async trackUsage(key, action = 'viewed') {
        try {
            // Send to analytics
            if (browser && window.analytics && window.analytics.track) {
                window.analytics.track('Feature Usage', {
                    feature_key: key,
                    feature_value: this.getFlag(key),
                    action: action
                });
            }
        } catch (err) {
            console.error('Failed to track feature usage:', err);
        }
    }
    
    /**
     * Cache flags in localStorage
     */
    cacheFlags(flags) {
        if (!browser) return;
        
        try {
            const cache = {
                flags: flags,
                timestamp: Date.now()
            };
            localStorage.setItem(this.cacheKey, JSON.stringify(cache));
        } catch (err) {
            console.error('Failed to cache feature flags:', err);
        }
    }
    
    /**
     * Get cached flags if valid
     */
    getCachedFlags() {
        if (!browser) return null;
        
        try {
            const cached = localStorage.getItem(this.cacheKey);
            if (!cached) return null;
            
            const data = JSON.parse(cached);
            const age = Date.now() - data.timestamp;
            
            if (age < this.cacheTTL) {
                return data.flags;
            }
            
            // Cache expired
            localStorage.removeItem(this.cacheKey);
            return null;
            
        } catch (err) {
            console.error('Failed to get cached flags:', err);
            return null;
        }
    }
    
    /**
     * Clear cache
     */
    clearCache() {
        if (!browser) return;
        
        try {
            localStorage.removeItem(this.cacheKey);
        } catch (err) {
            console.error('Failed to clear cache:', err);
        }
    }
    
    /**
     * Subscribe to flag updates
     */
    subscribe(callback) {
        return this.flags.subscribe(callback);
    }
}

// Create singleton instance
const featureFlags = new FeatureFlagsClient();

// Helper functions for common use cases
export function isFeatureEnabled(key) {
    return featureFlags.isEnabled(key);
}

export function getFeatureVariant(key, defaultVariant = 'control') {
    return featureFlags.getVariant(key, defaultVariant);
}

export function trackFeatureUsage(key, action = 'viewed') {
    return featureFlags.trackUsage(key, action);
}

// Svelte store for reactive updates
export const flags = featureFlags.flags;
export const flagsLoading = featureFlags.loading;
export const flagsError = featureFlags.error;

export default featureFlags;