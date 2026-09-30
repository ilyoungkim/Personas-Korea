<template>
  <section class="p-6 border-t border-slate-800">
    <h2 class="text-lg font-semibold mb-3">MCP Test</h2>
    <p class="text-sm text-slate-400 mb-4">
      MCP 서버(streamable-http)를 통해 직접 테스트합니다. 대시보드는 DB에 직접 접속하지 않습니다.
    </p>

    <!-- 툴 목록 로드 -->
    <div class="flex gap-2 mb-4">
      <button @click="loadTools" class="bg-slate-700 hover:bg-slate-600 rounded px-4 py-2 text-sm font-semibold">
        {{ loadingTools ? '로딩 중...' : '툴 목록 불러오기' }}
      </button>
      <span v-if="toolsError" class="text-red-400 text-sm self-center">{{ toolsError }}</span>
    </div>

    <!-- 툴 카드 목록 (이름 + 설명) -->
    <div v-if="tools.length" class="grid md:grid-cols-2 gap-3 mb-6">
      <button
        v-for="t in tools"
        :key="t.name"
        @click="selectTool(t)"
        class="text-left rounded-lg border p-3 transition-colors"
        :class="selectedTool === t.name ? 'border-emerald-500 bg-emerald-900/20' : 'border-slate-800 bg-slate-900 hover:border-slate-600'"
      >
        <div class="font-semibold text-sm text-slate-100">{{ t.name }}</div>
        <div class="text-xs text-slate-400 mt-1 whitespace-pre-line">{{ t.description }}</div>
      </button>
    </div>

    <!-- 선택된 툴 상세 -->
    <div v-if="selectedToolInfo" class="mb-4 rounded-lg bg-slate-900 border border-slate-800 p-4">
      <div class="font-semibold text-sm text-emerald-400 mb-1">{{ selectedToolInfo.name }}</div>
      <div class="text-sm text-slate-300 whitespace-pre-line mb-3">{{ selectedToolInfo.description }}</div>

      <!-- 파라미터 힌트 -->
      <div v-if="paramHints.length" class="mb-3">
        <div class="text-xs font-semibold text-slate-400 mb-1">입력 파라미터</div>
        <div class="flex flex-wrap gap-2">
          <span v-for="p in paramHints" :key="p.name" class="text-xs px-2 py-1 rounded bg-slate-800">
            {{ p.name }}<span class="text-slate-500">: {{ p.type }}</span>
            <span v-if="p.required" class="text-red-400">*</span>
          </span>
        </div>
      </div>

      <button @click="fillTemplate()" class="text-xs text-emerald-400 hover:text-emerald-300 mr-3">인자 템플릿 채우기</button>
      <button @click="clearArgs" class="text-xs text-slate-400 hover:text-slate-300">비우기</button>
    </div>

    <!-- 인자 입력 -->
    <div v-if="selectedTool" class="mb-4">
      <label class="block text-sm text-slate-400 mb-1">Arguments (JSON)</label>
      <textarea v-model="argsText" rows="6"
                class="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm font-mono"></textarea>
      <p class="text-xs text-slate-500 mt-1">JSON 형식으로 입력. 예: {"query": "자녀 교육", "province": "경기"}</p>
    </div>

    <!-- 실행 버튼 -->
    <div v-if="selectedTool" class="flex gap-2 mb-4">
      <button @click="runTool" class="bg-emerald-600 hover:bg-emerald-500 rounded px-4 py-2 text-sm font-semibold">
        {{ running ? '실행 중...' : '실행' }}
      </button>
    </div>

    <!-- 오류 -->
    <div v-if="resultError" class="mb-4 p-3 rounded bg-red-900/50 text-red-300 text-sm">
      {{ resultError }}
    </div>

    <!-- 결과 -->
    <div v-if="result" class="mb-4">
      <h3 class="text-sm font-semibold text-slate-300 mb-2">결과</h3>
      <pre class="bg-slate-900 border border-slate-800 rounded p-4 text-xs overflow-auto max-h-96">{{ resultText }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
interface Tool { name: string; description: string; inputSchema?: any }

const tools = ref<Tool[]>([])
const toolsError = ref('')
const loadingTools = ref(false)
const selectedTool = ref('')
const argsText = ref('{}')
const result = ref<any>(null)
const resultError = ref('')
const running = ref(false)

const selectedToolInfo = computed(() => tools.value.find((t) => t.name === selectedTool.value) || null)

// inputSchema에서 파라미터 힌트 추출
const paramHints = computed(() => {
  const schema = selectedToolInfo.value?.inputSchema
  if (!schema || !schema.properties) return []
  const required: string[] = schema.required || []
  return Object.entries(schema.properties).map(([name, def]: [string, any]) => ({
    name,
    type: def?.type || 'any',
    required: required.includes(name),
  }))
})

const resultText = computed(() => (result.value != null ? JSON.stringify(result.value, null, 2) : ''))

// 툴별 유용한 기본 인자값 (바로 실행 가능한 예시)
const DEFAULT_ARGS: Record<string, Record<string, any>> = {
  search_persona: { province: '경기', age_min: 40, age_max: 49, sex: '여자', limit: 5 },
  aggregate_persona: { province: '경기', age_min: 40, age_max: 49, sex: '여자' },
  similar_persona: { query: '자녀 교육과 건강관리에 관심이 많은 맞벌이 여성', province: '경기', sex: '여자', limit: 5 },
  cluster_summary: { limit: 10 },
  cluster_detail: { cluster_id: 'C017' },
  core_persona_summary: {},
  core_persona_detail: { core_id: 'P05' },
  compare_persona: {
    group_a: { label: '서울 30대 여성 1인가구', sex: '여자', province: '서울', age_min: 30, age_max: 39, family_type: '혼자 거주' },
    group_b: { label: '경기 40대 여성 자녀가구', sex: '여자', province: '경기', age_min: 40, age_max: 49, family_type: '배우자·자녀와 거주' },
  },
}

function selectTool(t: Tool) {
  selectedTool.value = t.name
  fillTemplate(t)
}

function fillTemplate(t?: Tool) {
  const info = t || selectedToolInfo.value
  if (!info) return
  const toolName = info.name

  // 1) 툴별 기본값이 있으면 우선 사용
  if (DEFAULT_ARGS[toolName]) {
    argsText.value = JSON.stringify(DEFAULT_ARGS[toolName], null, 2)
    return
  }

  // 2) 없으면 inputSchema 기반 템플릿 생성
  const schema = info.inputSchema
  if (!schema || !schema.properties) {
    argsText.value = '{}'
    return
  }
  const template: Record<string, any> = {}
  for (const [name, def] of Object.entries(schema.properties)) {
    const d: any = def
    if (d?.default !== undefined) template[name] = d.default
    else if (d?.type === 'integer' || d?.type === 'number') template[name] = 0
    else if (d?.type === 'boolean') template[name] = false
    else if (d?.type === 'array') template[name] = []
    else if (d?.type === 'object') template[name] = {}
    else template[name] = ''
  }
  argsText.value = JSON.stringify(template, null, 2)
}

function clearArgs() {
  argsText.value = '{}'
}

async function loadTools() {
  loadingTools.value = true
  toolsError.value = ''
  try {
    const { data } = await useFetch('/api/mcp/tools')
    if (data.value?.ok) {
      tools.value = data.value.tools || []
    } else {
      toolsError.value = data.value?.error || '툴 목록 조회 실패'
    }
  } catch (e: any) {
    toolsError.value = e.message
  } finally {
    loadingTools.value = false
  }
}

async function runTool() {
  running.value = true
  result.value = null
  resultError.value = ''
  let args: any = {}
  try {
    args = JSON.parse(argsText.value || '{}')
  } catch {
    resultError.value = 'Arguments가 유효한 JSON이 아닙니다.'
    running.value = false
    return
  }
  try {
    const { data } = await useFetch('/api/mcp/call', {
      method: 'POST',
      body: { toolName: selectedTool.value, args },
    })
    if (data.value?.ok) {
      result.value = data.value.result
    } else {
      resultError.value = data.value?.error || '실행 실패'
    }
  } catch (e: any) {
    resultError.value = e.message
  } finally {
    running.value = false
  }
}
</script>
