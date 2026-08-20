// "checked 3:37:04 pm" -- the backend gives an ISO timestamp, not this
// phrase; formatted here the way expires_in is pre-formatted server-side.
export function formatCheckedAt(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" }).toLowerCase();
}
