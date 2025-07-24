export interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag: string;
  dateFormat: string;
  numberFormat: {
    decimal: string;
    thousands: string;
  };
  currency: {
    code: string;
    symbol: string;
    position: 'before' | 'after';
  };
}

export const languages: Record<string, Language> = {
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
    dateFormat: 'MM/DD/YYYY',
    numberFormat: {
      decimal: '.',
      thousands: ','
    },
    currency: {
      code: 'USD',
      symbol: '$',
      position: 'before'
    }
  },
  es: {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    },
    currency: {
      code: 'EUR',
      symbol: '€',
      position: 'after'
    }
  },
  pt: {
    code: 'pt',
    name: 'Portuguese',
    nativeName: 'Português',
    flag: '🇧🇷',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    },
    currency: {
      code: 'BRL',
      symbol: 'R$',
      position: 'before'
    }
  },
  id: {
    code: 'id',
    name: 'Indonesian',
    nativeName: 'Bahasa Indonesia',
    flag: '🇮🇩',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: {
      decimal: ',',
      thousands: '.'
    },
    currency: {
      code: 'IDR',
      symbol: 'Rp',
      position: 'before'
    }
  }
};

export const defaultLanguage = 'en';
export const supportedLanguages = Object.keys(languages);

export function getLanguage(code: string): Language {
  return languages[code] || languages[defaultLanguage];
}