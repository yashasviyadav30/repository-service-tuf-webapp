// Shared by every page's mock endpoints so mocked calls feel like real
// network requests (loading states actually show up) instead of resolving
// instantly.
export function simulateLatency(ms = 300): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
