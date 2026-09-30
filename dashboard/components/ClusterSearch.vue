<template>
  <section class="p-6">
    <h2 class="text-lg font-semibold mb-3">클러스터 정보 검색</h2>

    <!-- 검색 타입 선택 -->
    <div class="flex flex-wrap gap-2 mb-4">
      <button
        v-for="opt in searchTypes"
        :key="opt.key"
        @click="setType(opt.key)"
        class="px-3 py-2 rounded text-sm font-semibold transition-colors"
        :class="type === opt.key ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- 입력 -->
    <div class="flex flex-wrap gap-2 mb-4">
      <input
        v-if="needsId"
        v-model="inputId"
        :placeholder="idPlaceholder"
        class="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm w-48"
      />
      <input
        v-if="needsLimit"
        v-model="inputLimit"
        type="number"
        placeholder="개수"
        class="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm w-24"
      />
      <button @click="search" class="bg-emerald-600 hover:bg-emerald-500 rounded px-4 py-2 text-sm font-semibold">
        {{ loading ? '조회 중...' : '조회' }}
      </button>
    </div>

    <!-- 오류 -->
    <div v-if="error" class="mb-4 p-3 rounded bg-red-900/50 text-red-300 text-sm">{{ error }}</div>

    <!-- 결과 -->
    <div v-if="result" class="space-y-3">
      <!-- 요약 (cluster_summary / core_persona_summary) -->
      <div v-if="isSummary" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-slate-400 border-b border-slate-800">
              <th class="py-2 pr-4">ID</th>
              <th class="py-2 pr-4">라벨</th>
              <th class="py-2 pr-4 text-right">인구</th>
              <th class="py-2 pr-4 text-right">비중</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in summaryList" :key="c.id" class="border-b border-slate-800/50">
              <td class="py-2 pr-4 text-slate-500">{{ c.id }}</td>
              <td class="py-2 pr-4">{{ c.label }}</td>
              <td class="py-2 pr-4 text-right">{{ c.population?.toLocaleString() }}</td>
              <td class="py-2 pr-4 text-right text-slate-400">{{ c.ratio }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 상세 (cluster_detail / core_persona_detail) -->
      <div v-else>
        <div class="rounded-lg bg-slate-900 border border-slate-800 p-4">
          <div class="font-semibold text-emerald-400 text-sm mb-1">{{ detailInfo?.label }}</div>
          <div class="text-xs text-slate-400">인구 {{ detailInfo?.population?.toLocaleString() }}명</div>
        </div>

        <!-- Major 분해 (core 상세) -->
        <div v-if="detailMajors?.length" class="mt-3">
          <h3 class="text-sm font-semibold text-slate-300 mb-2">하위 Major 분해</h3>
          <div class="space-y-1">
            <div v-for="m in detailMajors" :key="m.major_id" class="text-xs text-slate-400">
              {{ m.major_id }} · {{ m.label }} — {{ m.population?.toLocaleString() }}명
            </div>
          </div>
        </div>

        <!-- 샘플 -->
        <div v-if="detailSamples?.length" class="mt-3">
          <h3 class="text-sm font-semibold text-slate-300 mb-2">대표 페르소나 샘플</h3>
          <div class="space-y-2">
            <div v-for="s in detailSamples" :key="s.uuid" class="rounded bg-slate-900 border border-slate-800 p-3">
              <div class="flex gap-2 flex-wrap text-xs mb-1">
                <span class="px-2 py-1 rounded bg-slate-800">{{ s.sex }}</span>
                <span class="px-2 py-1 rounded bg-slate-800">{{ s.age }}세</span>
                <span class="px-2 py-1 rounded bg-slate-800">{{ s.province }} {{ s.district }}</span>
                <span class="px-2 py-1 rounded bg-slate-800">{{ s.occupation }}</span>
              </div>
              <p class="text-xs text-slate-300">{{ s.persona }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const searchTypes = [
  { key: 'cluster_summary', label: '클러스터 목록' },
  { key: 'cluster_detail', label: '클러스터 상세' },
  { key: 'core_persona_summary', label: 'Core Persona 목록' },
  { key: 'core_persona_detail', label: 'Core Persona 상세' },
]

const type = ref('cluster_summary')
const inputId = ref('')
const inputLimit = ref('10')
const result = ref<any>(null)
const error = ref('')
const loading = ref(false)

const needsId = computed(() => type.value.endsWith('_detail'))
const needsLimit = computed(() => type.value.endsWith('_summary'))
const idPlaceholder = computed(() => (type.value === 'cluster_detail' ? '클러스터 ID (예: C017)' : 'Core ID (예: P05)'))

const isSummary = computed(() => type.value.endsWith('_summary'))

// summary 결과 → 리스트로 변환
const summaryList = computed(() => {
  if (!result.value) return []
  if (type.value === 'cluster_summary') {
    return (result.value.top_clusters || []).map((c: any) => ({
      id: c.cluster_id,
      label: c.label,
      population: c.population,
      ratio: c.population_ratio ? (c.population_ratio * 100).toFixed(1) : '0.0',
    }))
  }
  if (type.value === 'core_persona_summary') {
    return (result.value.core_personas || []).map((c: any) => ({
      id: c.core_id,
      label: c.label,
      population: c.population,
      ratio: c.population_ratio ? (c.population_ratio * 100).toFixed(1) : '0.0',
    }))
  }
  return []
})

const detailInfo = computed(() => (result.value?.cluster || result.value?.core) || null)
const detailMajors = computed(() => result.value?.major_breakdown || [])
const detailSamples = computed(() => result.value?.samples || [])

function setType(k: string) {
  type.value = k
  result.value = null
  error.value = ''
  if (k === 'cluster_detail') inputId.value = 'C017'
  else if (k === 'core_persona_detail') inputId.value = 'P05'
  else if (k === 'cluster_summary') inputLimit.value = '10'
  else inputLimit.value = ''
}

async function search() {
  loading.value = true
  error.value = ''
  result.value = null

  let toolName = type.value
  let args: any = {}

  if (type.value === 'cluster_summary') args = { limit: parseInt(inputLimit.value) || 10 }
  else if (type.value === 'core_persona_summary') args = {}
  else if (type.value === 'cluster_detail') args = { cluster_id: inputId.value }
  else if (type.value === 'core_persona_detail') args = { core_id: inputId.value }

  try {
    const { data } = await useFetch('/api/mcp/call', {
      method: 'POST',
      body: { toolName, args },
    })
    if (data.value?.ok) {
      result.value = data.value.result
    } else {
      error.value = data.value?.error || '조회 실패'
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
