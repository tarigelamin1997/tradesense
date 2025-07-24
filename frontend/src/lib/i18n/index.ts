import { browser } from '$app/environment';
import { init, register, getLocaleFromNavigator } from 'svelte-i18n';
import { defaultLanguage, supportedLanguages } from './languages';

const STORAGE_KEY = 'tradesense-language';

// Register all language loaders
register('en', () => import('./locales/en/index'));
register('es', () => import('./locales/es/index'));
register('pt', () => import('./locales/pt/index'));
register('id', () => import('./locales/id/index'));

// Get saved language or detect from browser
export function getInitialLocale(): string {
  if (browser) {
    // Check localStorage first
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && supportedLanguages.includes(saved)) {
      return saved;
    }
    
    // Try to get from browser
    const browserLocale = getLocaleFromNavigator();
    if (browserLocale) {
      // Extract language code (e.g., 'es' from 'es-ES')
      const langCode = browserLocale.split('-')[0];
      if (supportedLanguages.includes(langCode)) {
        return langCode;
      }
    }
  }
  
  return defaultLanguage;
}

// Save language preference
export function saveLanguagePreference(locale: string) {
  if (browser) {
    localStorage.setItem(STORAGE_KEY, locale);
  }
}

// Initialize i18n
export async function initI18n() {
  const initialLocale = getInitialLocale();
  
  await init({
    fallbackLocale: defaultLanguage,
    initialLocale,
    loadingDelay: 200,
    formats: {
      number: {
        currency: {
          style: 'currency'
        }
      }
    }
  });
  
  return initialLocale;
}