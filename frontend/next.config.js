/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In production, the frontend talks directly to the backend via
    // NEXT_PUBLIC_API_URL — no rewrite proxy needed.
    if (process.env.NEXT_PUBLIC_API_URL) {
      return [];
    }
    // In development, proxy /api/* to the local backend so we don't need CORS.
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
