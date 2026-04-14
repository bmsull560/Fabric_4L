import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Locale = "en" | "es";

const translations = {
  en: {
    appShell: {
      platformName: "Value Fabric",
      platformTagline: "Intelligence Platform",
      searchPlaceholder: "Search entities, domains, cases…",
      modeSuffix: "mode",
      modes: {
        standard: "Standard",
        advanced: "Advanced",
        admin: "Admin",
      },
    },
    home: {
      title: "Welcome to Value Fabric",
      description:
        "Use the navigation to explore value models, evidence, and delivery workflows.",
      cta: "Open Command Center",
    },
    login: {
      signIn: "Sign In",
      cardDescription:
        "Enter your tenant identifier to sign in with your organization's SSO",
      tenantLabel: "Tenant Identifier",
      tenantPlaceholder: "e.g., acme-corp",
      tenantHelp: "This is your organization's unique identifier in Value Fabric",
      submit: "Sign In with SSO",
      submitting: "Signing In...",
      loading: "Loading...",
      authenticating: "Authenticating...",
      footer: "Contact your administrator if you don't know your tenant identifier",
      errors: {
        authFailed: "Authentication failed. Please try again.",
        authFailedGeneric: "Authentication failed",
        tenantRequired: "Please enter a tenant identifier",
        initiateFailed: "Failed to initiate login",
      },
    },
    notFound: {
      title: "Page Not Found",
      message:
        "Sorry, the page you are looking for doesn't exist. It may have been moved or deleted.",
      cta: "Go Home",
    },
  },
  es: {
    appShell: {
      platformName: "Value Fabric",
      platformTagline: "Plataforma de Inteligencia",
      searchPlaceholder: "Buscar entidades, dominios y casos…",
      modeSuffix: "modo",
      modes: {
        standard: "Estándar",
        advanced: "Avanzado",
        admin: "Administrador",
      },
    },
    home: {
      title: "Bienvenido a Value Fabric",
      description:
        "Usa la navegación para explorar modelos de valor, evidencia y flujos de entrega.",
      cta: "Abrir Command Center",
    },
    login: {
      signIn: "Iniciar sesión",
      cardDescription:
        "Introduce el identificador de tu tenant para iniciar sesión con el SSO de tu organización",
      tenantLabel: "Identificador de tenant",
      tenantPlaceholder: "p. ej., acme-corp",
      tenantHelp:
        "Este es el identificador único de tu organización en Value Fabric",
      submit: "Iniciar sesión con SSO",
      submitting: "Iniciando sesión...",
      loading: "Cargando...",
      authenticating: "Autenticando...",
      footer:
        "Contacta a tu administrador si no conoces el identificador de tenant",
      errors: {
        authFailed: "La autenticación falló. Inténtalo de nuevo.",
        authFailedGeneric: "La autenticación falló",
        tenantRequired: "Introduce un identificador de tenant",
        initiateFailed: "No se pudo iniciar el acceso",
      },
    },
    notFound: {
      title: "Página no encontrada",
      message:
        "Lo sentimos, la página que buscas no existe. Es posible que se haya movido o eliminado.",
      cta: "Ir al inicio",
    },
  },
} as const;

const I18nContext = createContext<{
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
} | null>(null);

const translate = (locale: Locale, key: string): string => {
  const value = key
    .split(".")
    .reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object" && part in acc
          ? (acc as Record<string, unknown>)[part]
          : undefined,
      translations[locale],
    );

  return typeof value === "string" ? value : key;
};

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("en");
  const t = useCallback((key: string) => translate(locale, key), [locale]);

  const contextValue = useMemo(
    () => ({
      locale,
      setLocale,
      t,
    }),
    [locale, t],
  );

  return (
    <I18nContext.Provider value={contextValue}>{children}</I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}
