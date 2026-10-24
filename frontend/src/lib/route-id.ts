"use client";

import { useParams, usePathname } from "next/navigation";

/**
 * The id placeholder the static export is built with. A static site is a folder of
 * pre-built HTML files, so it cannot know every candidate or job id in advance: each
 * dynamic page is built ONCE, for this placeholder, and the hosting layer serves that same
 * file for every real id (see render.yaml and frontend/scripts/serve-export.mjs).
 */
export const STATIC_PLACEHOLDER_ID = "_";

/**
 * The id of the record the current dynamic page is about.
 *
 * Normally Next supplies it as a route param. In the static export the param is the
 * placeholder, because the page was built for the placeholder, so the real id is read from
 * the address bar instead: every dynamic route in this app has the shape
 * `/<section>/<id>[/...]`, so it is the second path segment.
 */
export function useRouteId(): string {
  const params = useParams<{ id?: string }>();
  const pathname = usePathname();

  const fromParams = params?.id;
  if (fromParams && fromParams !== STATIC_PLACEHOLDER_ID) return fromParams;

  const segments = (pathname ?? "").split("/").filter(Boolean);
  return segments[1] ?? "";
}
