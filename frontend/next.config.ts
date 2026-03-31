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
  // Removed __dirname since it causes ReferenceError in ES modules
};

export default nextConfig;
