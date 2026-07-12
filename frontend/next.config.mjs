/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy /api to the backend so the browser talks to a single origin.
    const api =
      process.env.BACKEND_INTERNAL_URL ||
      (process.env.NODE_ENV === "production" ? "http://api:8000" : "http://localhost:8000");
    return [
      { source: "/api/:path*", destination: `${api}/api/:path*` },
      { source: "/health", destination: `${api}/health` },
    ];
  },
};

export default nextConfig;
