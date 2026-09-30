<template>
  <section class="p-6 border-t border-slate-800">
    <h2 class="text-lg font-semibold mb-3">API 호출 매뉴얼</h2>

    <div class="space-y-6">
      <!-- 대시보드 REST API -->
      <div>
        <h3 class="text-sm font-semibold text-emerald-400 mb-2">1. 대시보드 REST API</h3>
        <p class="text-xs text-slate-500 mb-2">대시보드 자체 API (PostgreSQL 직접 접근). 예: http://192.168.31.253:18080</p>
        <div class="space-y-2">
          <ApiRow v-for="r in restApis" :key="r.path" :method="r.method" :path="r.path" :desc="r.desc" :example="r.example" />
        </div>
      </div>

      <!-- MCP API -->
      <div>
        <h3 class="text-sm font-semibold text-sky-400 mb-2">2. MCP 서버 (streamable-http)</h3>
        <p class="text-xs text-slate-500 mb-2">MCP 프로토콜. 예: http://192.168.31.253:19000/mcp</p>
        <div class="space-y-2">
          <ApiRow v-for="r in mcpApis" :key="r.path" :method="r.method" :path="r.path" :desc="r.desc" :example="r.example" />
        </div>
      </div>

      <!-- MCP 툴 목록 -->
      <div>
        <h3 class="text-sm font-semibold text-slate-300 mb-2">3. MCP 툴 (8개)</h3>
        <div class="grid md:grid-cols-2 gap-2">
          <div v-for="t in toolList" :key="t.name" class="rounded bg-slate-900 border border-slate-800 p-2">
            <div class="text-xs font-semibold text-slate-200">{{ t.name }}</div>
            <div class="text-xs text-slate-500">{{ t.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const restApis = [
  {
    method: 'GET',
    path: '/api/stats',
    desc: '전체 통계 (총 인구, 지역/성별/연령 분포)',
    example: 'curl http://192.168.31.253:18080/api/stats',
  },
  {
    method: 'GET',
    path: '/api/search?province=경기&age_min=40&age_max=49&sex=여자&limit=20',
    desc: '구조화 조건 검색',
    example: `curl 'http://192.168.31.253:18080/api/search?province=경기&sex=여자&limit=5'`,
  },
  {
    method: 'GET',
    path: '/api/similar?q=자녀 교육',
    desc: '키워드 의미 검색 (LIKE 기반)',
    example: `curl 'http://192.168.31.253:18080/api/similar?q=자녀%20교육'`,
  },
]

const mcpApis = [
  {
    method: 'GET',
    path: '/api/mcp/tools',
    desc: 'MCP 툴 목록 조회 (대시보드가 MCP 경유)',
    example: 'curl http://192.168.31.253:18080/api/mcp/tools',
  },
  {
    method: 'POST',
    path: '/api/mcp/call',
    desc: 'MCP 툴 실행 (대시보드가 MCP 경유)',
    example: `curl -X POST http://192.168.31.253:18080/api/mcp/call -H 'Content-Type: application/json' -d '{"toolName":"aggregate_persona","args":{"province":"경기","sex":"여자"}}'`,
  },
]

const toolList = [
  { name: 'search_persona', desc: '구조화 조건 검색' },
  { name: 'aggregate_persona', desc: '집단 통계' },
  { name: 'similar_persona', desc: '하이브리드 의미+조건 검색' },
  { name: 'compare_persona', desc: '두 집단 비교' },
  { name: 'cluster_summary', desc: 'Micro 클러스터 목록' },
  { name: 'cluster_detail', desc: '클러스터 상세+샘플' },
  { name: 'core_persona_summary', desc: 'Core Persona 요약 (12개)' },
  { name: 'core_persona_detail', desc: 'Core 상세+Major 분해' },
]
</script>
