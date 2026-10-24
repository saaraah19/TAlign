/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  typedRoutes: true,

  // The product ships as a STATIC SITE (a folder of pre-built files) so the host can serve it
  // from a CDN that never sleeps; only the API behind it can be asleep. This is why there is no
  // middleware and why dynamic pages are built once for a placeholder id
  // (see src/lib/route-id.ts).
  // Only for production builds: the development server (`npm run dev`, used by docker compose)
  // must serve any record id on demand, which `output: "export"` forbids in dev.
  output: process.env.NODE_ENV === "production" ? "export" : undefined,
  trailingSlash: true, // /pipeline/_/index.html: the layout every static host serves without configuration
  images: { unoptimized: true },
};

module.exports = nextConfig;
