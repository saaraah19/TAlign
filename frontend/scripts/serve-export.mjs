// Serves the static export (frontend/out) the way Render serves a static site, and proxies
// /api/* to the backend, so the production build can be tried locally without Render.
//
//   npm run build && node scripts/serve-export.mjs
//
// Environment: PORT (default 3000), BACKEND_URL (default http://127.0.0.1:8000).
// Rules come from static-host-rules.json. Render's semantics, as documented: a file that exists
// is served first; otherwise the first matching rewrite rule applies; otherwise 404.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(root, "out");
const PORT = Number(process.env.PORT ?? 3000);
const BACKEND = new URL(process.env.BACKEND_URL ?? "http://127.0.0.1:8000");
const { rewrites } = JSON.parse(fs.readFileSync(path.join(root, "static-host-rules.json"), "utf8"));

const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".txt": "text/plain; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon",
  ".woff2": "font/woff2", ".map": "application/json",
};

function matches(source, pathname) {
  if (source.endsWith("/*")) return pathname.startsWith(source.slice(0, -1));
  const s = source.split("/"), p = pathname.split("/");
  return s.length === p.length && s.every((part, i) => part.startsWith(":") || part === p[i]);
}

function resolveFile(pathname) {
  const safe = path.normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, "");
  const candidates = [path.join(OUT, safe)];
  if (pathname.endsWith("/")) candidates.unshift(path.join(OUT, safe, "index.html"));
  else candidates.push(path.join(OUT, safe, "index.html"), path.join(OUT, safe + ".html"));
  return candidates.find((c) => c.startsWith(OUT) && fs.existsSync(c) && fs.statSync(c).isFile());
}

function send(res, file) {
  res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] ?? "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
}

function proxy(req, res) {
  const upstream = http.request(
    { host: BACKEND.hostname, port: BACKEND.port, method: req.method, path: req.url,
      headers: { ...req.headers, host: BACKEND.host } },
    (up) => { res.writeHead(up.statusCode ?? 502, up.headers); up.pipe(res); },
  );
  upstream.on("error", () => { // the backend is asleep or down: what a gateway would answer
    res.writeHead(502, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ detail: "Bad gateway" }));
  });
  req.pipe(upstream);
}

http.createServer((req, res) => {
  const { pathname } = new URL(req.url, "http://x");
  if (pathname.startsWith("/api/")) return proxy(req, res);
  const file = resolveFile(pathname);
  if (file) return send(res, file);
  const rule = rewrites.find((r) => matches(r.source, pathname));
  if (rule) {
    const target = resolveFile(rule.destination);
    if (target) return send(res, target);
  }
  const notFound = path.join(OUT, "404.html");
  res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
  if (fs.existsSync(notFound)) fs.createReadStream(notFound).pipe(res);
  else res.end("Not found");
}).listen(PORT, () => console.log(`static export on http://localhost:${PORT} -> API ${BACKEND.origin}`));
