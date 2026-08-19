// Jest substitute for env.ts (see jest.config.cjs moduleNameMapper).
// Mirrors .env.development -- tests never hit a real backend.
export const useMocks = true;
export const apiBaseUrl = "/api";
