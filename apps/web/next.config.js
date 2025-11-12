const withNextIntl = require('next-intl/plugin')('./i18n/config.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@tribi/ui"],
}

module.exports = withNextIntl(nextConfig);