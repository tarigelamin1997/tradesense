import { r as registerLocaleLoader, i as init } from "./runtime.js";
const languages = {
  en: {
    code: "en",
    name: "English",
    nativeName: "English",
    flag: "🇺🇸",
    dateFormat: "MM/DD/YYYY",
    numberFormat: {
      decimal: ".",
      thousands: ","
    },
    currency: {
      code: "USD",
      symbol: "$",
      position: "before"
    }
  },
  es: {
    code: "es",
    name: "Spanish",
    nativeName: "Español",
    flag: "🇪🇸",
    dateFormat: "DD/MM/YYYY",
    numberFormat: {
      decimal: ",",
      thousands: "."
    },
    currency: {
      code: "EUR",
      symbol: "€",
      position: "after"
    }
  },
  pt: {
    code: "pt",
    name: "Portuguese",
    nativeName: "Português",
    flag: "🇧🇷",
    dateFormat: "DD/MM/YYYY",
    numberFormat: {
      decimal: ",",
      thousands: "."
    },
    currency: {
      code: "BRL",
      symbol: "R$",
      position: "before"
    }
  },
  id: {
    code: "id",
    name: "Indonesian",
    nativeName: "Bahasa Indonesia",
    flag: "🇮🇩",
    dateFormat: "DD/MM/YYYY",
    numberFormat: {
      decimal: ",",
      thousands: "."
    },
    currency: {
      code: "IDR",
      symbol: "Rp",
      position: "before"
    }
  }
};
const defaultLanguage = "en";
registerLocaleLoader("en", () => import("./index4.js"));
registerLocaleLoader("es", () => import("./index5.js"));
registerLocaleLoader("pt", () => import("./index6.js"));
registerLocaleLoader("id", () => import("./index7.js"));
function getInitialLocale() {
  return defaultLanguage;
}
async function initI18n() {
  const initialLocale = getInitialLocale();
  await init({
    fallbackLocale: defaultLanguage,
    initialLocale,
    loadingDelay: 200,
    formats: {
      number: {
        currency: {
          style: "currency"
        }
      }
    }
  });
  return initialLocale;
}
export {
  initI18n as i,
  languages as l
};
