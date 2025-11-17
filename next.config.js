/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    experimental: { typedRoutes: true },
    env: {
        NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL
    }
};

console.log("NEXT_PUBLIC_API_BASE_URL at build:", process.env.NEXT_PUBLIC_API_BASE_URL);

module.exports = nextConfig;