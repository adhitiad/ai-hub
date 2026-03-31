import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  reactCompiler: true,
  // Turbopack warning fix
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
