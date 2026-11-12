/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_PAYPAL_CLIENT_ID?: string;
  readonly VITE_PAYPAL_CURRENCY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
