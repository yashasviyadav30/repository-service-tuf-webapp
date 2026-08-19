import type { Plugin } from "vite";
import { simulateLatency } from "./src/lib/mockDelay";
import { mockOverviewValid } from "./src/shared/overview/mocks/overviewMock";
import { mockStatusReady } from "./src/pages/Status/endpoints/mocks/statusMock";
import { mockRoleDetail } from "./src/pages/Roles/endpoints/mocks/roleMock";
import { mockRoots } from "./src/pages/RootHistory/endpoints/mocks/rootsMock";
import { mockAllArtifacts } from "./src/pages/Artifacts/endpoints/mocks/artifactsMock";

// Dev-only: answers /api/v1/* with the same fixtures the test suite uses,
// so `npm run dev` and demos work before a real backend exists.
// Application code never branches on mocks -- it always calls the real
// API; this stands in for that API locally, gated by VITE_USE_MOCKS.
export function mockApiPlugin(): Plugin {
  return {
    name: "mock-api",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url ?? "";

        const respond = async (body: unknown) => {
          await simulateLatency();
          res.setHeader("Content-Type", "application/json");
          res.end(JSON.stringify(body));
        };

        if (url === "/api/v1/overview" || url.startsWith("/api/v1/overview?")) {
          void respond(mockOverviewValid);
          return;
        }
        if (url === "/api/v1/status") {
          void respond(mockStatusReady);
          return;
        }
        if (url === "/api/v1/roots" || url.startsWith("/api/v1/roots?")) {
          void respond(mockRoots);
          return;
        }
        const roleMatch = /^\/api\/v1\/roles\/([^/?]+)$/.exec(url);
        if (roleMatch) {
          const role = roleMatch[1];
          void respond({ ...mockRoleDetail, name: role, raw_url: `/api/v1/roles/${role}/raw` });
          return;
        }
        if (url === "/api/v1/artifacts" || url.startsWith("/api/v1/artifacts?")) {
          // Only endpoint with real filtering logic -- search/paging
          // belongs in the dev-only mock server, not in application code.
          const params = new URL(url, "http://localhost").searchParams;
          const search = (params.get("search") ?? "").toLowerCase();
          const role = params.get("role") ?? "";
          const page = Number(params.get("page") ?? "1");
          const pageSize = Number(params.get("page_size") ?? "50");

          const filtered = mockAllArtifacts.filter(
            (artifact) => (!search || artifact.path.toLowerCase().includes(search)) && (!role || artifact.role === role),
          );
          const start = (page - 1) * pageSize;

          void respond({
            total: filtered.length,
            page,
            page_size: pageSize,
            artifacts: filtered.slice(start, start + pageSize),
            unavailable: [],
          });
          return;
        }

        next();
      });
    },
  };
}
