/** @type {import('jest').Config} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.ts"],
  testPathIgnorePatterns: ["/node_modules/", "/e2e/"],
  // ts-jest can't parse import.meta -- only src/lib/env.ts touches it, so
  // any specifier resolving to that file (bare "./env" from within lib/
  // itself, or "../lib/env" from elsewhere) is redirected to its Jest-safe
  // twin instead.
  moduleNameMapper: {
    "(^\\./env$)|(/lib/env$)": "<rootDir>/src/lib/env.mock",
  },
};
