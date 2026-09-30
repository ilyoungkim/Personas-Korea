export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const mcpUrl = config.mcpUrl || 'http://mcp:19000/mcp'

  const init = await mcpInitialize(mcpUrl)
  if (!init.ok || !init.sessionId) {
    return { ok: false, error: init.error || 'MCP 초기화 실패' }
  }

  const res = await mcpListTools(mcpUrl, init.sessionId)
  if (!res.ok) {
    return { ok: false, error: res.error }
  }

  // res.content 는 tools/list 결과(JSON string) → raw에서 파싱
  let tools: any[] = []
  const raw: any = res.raw
  if (raw && Array.isArray(raw.tools)) {
    tools = raw.tools
  } else if (res.content) {
    try {
      const parsed = JSON.parse(res.content)
      if (Array.isArray(parsed.tools)) tools = parsed.tools
    } catch {
      // ignore
    }
  }

  return {
    ok: true,
    sessionId: init.sessionId,
    tools: tools.map((t: any) => ({
      name: t.name,
      description: t.description || '',
      inputSchema: t.inputSchema || null,
    })),
  }
})
