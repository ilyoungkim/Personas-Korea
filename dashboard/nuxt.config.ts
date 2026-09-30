export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: false },
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    pgDsn: process.env.PG_DSN || 'postgresql://persona:persona@postgres:5432/persona',
    mcpUrl: process.env.MCP_URL || 'http://mcp:19000/mcp',
  },
  nitro: {
    host: '0.0.0.0',
    port: 18080,
  },
})
