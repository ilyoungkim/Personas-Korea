// MCP streamable-http 클라이언트 (Nitro 서버 전용)
// 대시보드는 DB에 직접 접속하지 않고, 반드시 MCP 서버를 통해 테스트한다.

interface McpCallResult {
  ok: boolean
  error?: string
  sessionId?: string
  content?: string
  raw?: any
}

function parseSse(text: string): any[] {
  const messages: any[] = []
  for (const line of text.split('\n')) {
    const trimmed = line.trim()
    if (trimmed.startsWith('data:')) {
      const data = trimmed.slice(5).trim()
      if (data && data !== '[DONE]') {
        try {
          messages.push(JSON.parse(data))
        } catch {
          // ignore non-json
        }
      }
    }
  }
  return messages
}

export async function mcpCall(
  mcpUrl: string,
  method: string,
  params: Record<string, any> = {},
  sessionId?: string
): Promise<McpCallResult> {
  const id = Date.now()
  const body = {
    jsonrpc: '2.0',
    id,
    method,
    params,
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
  }
  if (sessionId) headers['Mcp-Session-Id'] = sessionId

  let resp: Response
  try {
    resp = await fetch(mcpUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })
  } catch (e: any) {
    return { ok: false, error: `MCP 서버 연결 실패: ${e.message}` }
  }

  const newSessionId = resp.headers.get('Mcp-Session-Id') || resp.headers.get('mcp-session-id') || sessionId

  const text = await resp.text()

  if (!resp.ok) {
    return { ok: false, error: `HTTP ${resp.status}: ${text.slice(0, 200)}`, sessionId: newSessionId }
  }

  const contentType = resp.headers.get('content-type') || ''
  let messages: any[] = []

  if (contentType.includes('text/event-stream')) {
    messages = parseSse(text)
  } else {
    try {
      const parsed = JSON.parse(text)
      messages = [parsed]
    } catch {
      messages = []
    }
  }

  // result/error 메시지 찾기
  const resultMsg = messages.find((m) => m && m.id === id)
  if (!resultMsg) {
    return { ok: false, error: '응답을 파싱할 수 없습니다', raw: messages, sessionId: newSessionId }
  }

  if (resultMsg.error) {
    return {
      ok: false,
      error: resultMsg.error.message || JSON.stringify(resultMsg.error),
      sessionId: newSessionId,
    }
  }

  // tools/call 결과에서 text content 추출
  let content: string | undefined
  const r = resultMsg.result
  if (r && r.content && Array.isArray(r.content)) {
    content = r.content
      .map((c: any) => (typeof c === 'string' ? c : c?.text || ''))
      .join('')
  } else if (r && typeof r === 'object') {
    content = JSON.stringify(r, null, 2)
  }

  return { ok: true, sessionId: newSessionId, content, raw: resultMsg.result }
}

// initialize → 세션 ID 획득
export async function mcpInitialize(mcpUrl: string): Promise<McpCallResult> {
  return mcpCall(mcpUrl, 'initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'persona-dashboard', version: '1.0' },
  })
}

// tools/list → 툴 목록 조회
export async function mcpListTools(mcpUrl: string, sessionId: string): Promise<McpCallResult> {
  return mcpCall(mcpUrl, 'tools/list', {}, sessionId)
}

// tools/call → 툴 실행
export async function mcpCallTool(
  mcpUrl: string,
  sessionId: string,
  toolName: string,
  args: Record<string, any> = {}
): Promise<McpCallResult> {
  return mcpCall(mcpUrl, 'tools/call', { name: toolName, arguments: args }, sessionId)
}
