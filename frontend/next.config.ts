import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["192.168.10.6", "10.121.85.126", "10.146.30.126", "127.0.0.1", "localhost"],
  turbopack: {
    root: path.join(__dirname, ".."),
  },
};

export default nextConfig;
