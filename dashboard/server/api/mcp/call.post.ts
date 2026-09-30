export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const mcpUrl = config.mcpUrl || 'http://mcp:19000/mcp'

  const body = await readBody(event)
  const toolName = body?.toolName
  const args = body?.args || {}

  if (!toolName) {
    return { ok: false, error: 'toolName 필수' }
  }

  // 1) initialize
  const init = await mcpInitialize(mcpUrl)
  if (!init.ok || !init.sessionId) {
    return { ok: false, error: init.error || 'MCP 초기화 실패' }
  }

  // 2) tools/call
  const res = await mcpCallTool(mcpUrl, init.sessionId, toolName, args)

  if (!res.ok) {
    return { ok: false, error: res.error }
  }

  // content를 JSON으로 파싱 시도 (MCP 툴 결과는 JSON string)
  let parsed: any = res.content
  if (typeof res.content === 'string') {
    try {
      parsed = JSON.parse(res.content)
    } catch {
      // plain text 그대로
    }
  }

  return { ok: true, tool: toolName, result: parsed }
})
