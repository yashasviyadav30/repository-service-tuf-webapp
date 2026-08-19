// Only file that touches import.meta.env directly -- Jest can't parse
// import.meta, so jest.config.cjs maps this specifier to env.mock.ts instead.
export const useMocks = import.meta.env.VITE_USE_MOCKS === "true";
export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";
