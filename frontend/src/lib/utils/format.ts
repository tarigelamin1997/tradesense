import { get } from 'svelte/store';
import { locale } from 'svelte-i18n';

// Get current locale with fallback
function getCurrentLocale(): string {
    try {
        return get(locale) || 'en';
    } catch {
        return 'en';
    }
}

export function formatCurrency(value: number, currency: string = 'USD'): string {
    const currentLocale = getCurrentLocale();
    return new Intl.NumberFormat(currentLocale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

export function formatPercent(value: number, decimals: number = 2): string {
    const currentLocale = getCurrentLocale();
    return new Intl.NumberFormat(currentLocale, {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value / 100);
}

export function formatNumber(value: number, decimals: number = 2): string {
    const currentLocale = getCurrentLocale();
    return new Intl.NumberFormat(currentLocale, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

export function formatDate(date: Date | string): string {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const currentLocale = getCurrentLocale();
    return new Intl.DateTimeFormat(currentLocale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(dateObj);
}

export function formatDateTime(date: Date | string): string {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const currentLocale = getCurrentLocale();
    return new Intl.DateTimeFormat(currentLocale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(dateObj);
}