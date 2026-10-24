import JobDetailPageClient from "./client";

/**
 * Static export: this page is built once, for a placeholder id, and the host serves the same
 * file for every real id. The client component reads the real id from the address bar
 * (see lib/route-id.ts).
 */
export function generateStaticParams() {
  return [{ id: "_" }];
}

export default function Page() {
  return <JobDetailPageClient />;
}
