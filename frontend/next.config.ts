import type { NextConfig } from "next";

// 后端地址：本地开发走 8000；生产默认连接现有线上后端，也允许环境变量覆盖。
const BACKEND_URL = process.env.BACKEND_URL ?? (
  process.env.NODE_ENV === "production"
    ? "https://sc0hshvaar6kuul9kb1pu.apigateway-cn-beijing.volceapi.com"
    : "http://127.0.0.1:8000"
);

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
