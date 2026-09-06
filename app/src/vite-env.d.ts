/// <reference types="vite/client" />

interface ImportMetaEnv {
    /** Backend origin. Defaults to http://localhost:8000. */
    readonly VITE_API_BASE_URL?: string;
    /** API key sent as X-API-Key. Visible in the bundle; single-operator use only. */
    readonly VITE_API_KEY?: string;
}
