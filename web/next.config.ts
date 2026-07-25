import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Pin the file-tracing root to this web project so Next.js does not infer a
  // different workspace root (which emits a warning) when the repo sits inside
  // a larger monorepo or alongside other lockfiles.
  outputFileTracingRoot: path.join(__dirname),
};

export default nextConfig;
