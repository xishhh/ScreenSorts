import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/data/:path*",
        destination: "http://localhost:8000/data/:path*",
      },
    ]
  },
}

export default nextConfig
