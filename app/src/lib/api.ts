/**
 * One place that talks to the backend.
 *
 * Every route except `/health` and `/ready` requires `X-API-Key`. The
 * components used to call `fetch('http://localhost:8000/...')` with no key, so
 * once the API was protected the dashboard showed empty tables and the demo
 * failed with "Failed to create lead" and no explanation.
 *
 * The key comes from `VITE_API_KEY` at build time, or from a value entered in
 * the UI (kept in sessionStorage for this tab only). Either way it is visible
 * to whoever can open the page: this dashboard is a single-operator tool, not
 * a multi-user product, and the README says so.
 */

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
    /\/+$/,
    '',
);

const STORAGE_KEY = 'outreach.apiKey';

export function getApiKey(): string {
    try {
        return sessionStorage.getItem(STORAGE_KEY) ?? import.meta.env.VITE_API_KEY ?? '';
    } catch {
        return import.meta.env.VITE_API_KEY ?? '';
    }
}

export function setApiKey(key: string): void {
    try {
        if (key) sessionStorage.setItem(STORAGE_KEY, key);
        else sessionStorage.removeItem(STORAGE_KEY);
    } catch {
        // Storage unavailable (private mode, blocked): the key is simply not remembered.
    }
}

export class ApiError extends Error {
    readonly status: number;

    constructor(status: number, message: string) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

function detailFrom(body: unknown, fallback: string): string {
    if (typeof body === 'object' && body !== null && 'detail' in body) {
        const detail = (body as { detail: unknown }).detail;
        if (typeof detail === 'string') return detail;
    }
    return fallback;
}

/** Fetch a JSON route with the API key attached; throws ApiError on a non-2xx. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    const key = getApiKey();
    if (key) headers.set('X-API-Key', key);
    if (init.body !== undefined && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
    if (!response.ok) {
        let detail = `${response.status} ${response.statusText}`;
        try {
            detail = detailFrom(await response.json(), detail);
        } catch {
            // Non-JSON error body; keep the status line.
        }
        throw new ApiError(response.status, detail);
    }
    return (await response.json()) as T;
}

export interface ReadyReport {
    ready: boolean;
    checks: Record<string, { ok: boolean; required: boolean; enabled?: boolean }>;
}

/** `/ready` needs no key and answers 503 when unready; both bodies are useful. */
export async function fetchReady(): Promise<ReadyReport | null> {
    try {
        const response = await fetch(`${API_BASE_URL}/ready`);
        return (await response.json()) as ReadyReport;
    } catch {
        return null;
    }
}
