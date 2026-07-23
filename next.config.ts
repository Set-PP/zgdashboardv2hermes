import type { NextConfig } from "next";

// Same-origin proxy to the pipeline API (FastAPI).
// Local dev: unused — api.ts hits NEXT_PUBLIC_PIPELINE_API (default http://127.0.0.1:8600) directly.
// VPS (docker-compose): NEXT_PUBLIC_PIPELINE_API=/pipe  →  /pipe/* proxies to the api container.
const PIPELINE_INTERNAL = process.env.PIPELINE_INTERNAL ?? "http://127.0.0.1:8600";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
    ],
  },
  async rewrites() {
    return [{ source: "/pipe/:path*", destination: `${PIPELINE_INTERNAL}/:path*` }];
  },
};

export default nextConfig;
