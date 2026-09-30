<template>
  <main class="min-h-screen bg-slate-950 text-slate-100">
    <header class="border-b border-slate-800 px-6 py-4">
      <h1 class="text-xl font-bold">Korea Persona Intelligence</h1>
      <p class="text-sm text-slate-400">1,000,000 한국 합성 페르소나 · 대시보드</p>
    </header>

    <section class="grid grid-cols-2 md:grid-cols-4 gap-4 p-6">
      <div class="rounded-lg bg-slate-900 p-4">
        <div class="text-3xl font-bold text-emerald-400">{{ (stats?.total ?? 0).toLocaleString() }}</div>
        <div class="text-sm text-slate-400">총 페르소나</div>
      </div>
    </section>

    <section class="grid md:grid-cols-3 gap-4 p-6">
      <BarCard title="지역 분포" :data="stats?.province" />
      <BarCard title="성별 분포" :data="stats?.sex" />
      <BarCard title="연령 분포" :data="stats?.age" />
    </section>

    <!-- 클러스터 정보 검색 -->
    <ClusterSearch />

    <!-- 집단 비교 -->
    <ComparePersona />

    <!-- 의미 검색 -->
    <section class="p-6">
      <h2 class="text-lg font-semibold mb-3">의미 검색</h2>
      <div class="flex gap-2 mb-4">
        <input v-model="simQuery" placeholder="예: 자녀 교육과 건강관리에 관심이 많은 40대 여성"
               class="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm" />
        <button @click="doSimilar" class="bg-emerald-600 hover:bg-emerald-500 rounded px-4 py-2 text-sm font-semibold">검색</button>
      </div>
      <div class="space-y-3">
        <div v-for="p in simResults" :key="p.uuid" class="rounded-lg bg-slate-900 p-4">
          <div class="flex gap-2 flex-wrap text-xs">
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.sex }}</span>
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.age }}세</span>
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.province }} {{ p.district }}</span>
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.occupation }}</span>
          </div>
          <p class="mt-2 text-sm text-slate-300">{{ p.persona }}</p>
        </div>
        <p v-if="simResults.length === 0" class="text-sm text-slate-500">검색 결과가 없습니다.</p>
      </div>
    </section>

    <!-- 구조화 검색 -->
    <section class="p-6">
      <h2 class="text-lg font-semibold mb-3">구조화 검색</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
        <input v-model="filters.province" placeholder="시도 (예: 경기)" class="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm" />
        <input v-model="filters.sex" placeholder="성별 (여자/남자)" class="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm" />
        <input v-model="filters.age_min" placeholder="최소 연령" class="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm" />
        <input v-model="filters.age_max" placeholder="최대 연령" class="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm" />
      </div>
      <button @click="doSearch" class="bg-emerald-600 hover:bg-emerald-500 rounded px-4 py-2 text-sm font-semibold">검색</button>
      <div class="mt-4 space-y-3">
        <div v-for="p in results" :key="p.uuid" class="rounded-lg bg-slate-900 p-4">
          <div class="flex gap-2 flex-wrap text-xs">
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.sex }}</span>
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.age }}세</span>
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.province }} {{ p.district }}</span>
            <span class="px-2 py-1 rounded bg-slate-800">{{ p.occupation }}</span>
          </div>
          <p class="mt-2 text-sm text-slate-300">{{ p.persona }}</p>
        </div>
        <p v-if="results.length === 0" class="text-sm text-slate-500">검색 결과가 없습니다.</p>
      </div>
    </section>

    <McpTest />

    <ApiManual />
  </main>
</template>

<script setup lang="ts">
interface Dist { key: string; cnt: number }
interface Stats { total: number; province: Dist[]; sex: Dist[]; age: Dist[] }

const stats = ref<Stats | null>(null)
const results = ref<any[]>([])
const simResults = ref<any[]>([])
const simQuery = ref('')
const filters = reactive({ province: '', sex: '', age_min: '', age_max: '' })

const { data: statsData } = await useFetch<Stats>('/api/stats')
stats.value = statsData.value ?? null

async function doSearch() {
  const qs = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => { if (v) qs.set(k, v) })
  const { data: d } = await useFetch(`/api/search?${qs}`)
  results.value = d.value?.results ?? []
}

async function doSimilar() {
  if (!simQuery.value.trim()) return
  const { data: d } = await useFetch(`/api/similar?q=${encodeURIComponent(simQuery.value)}`)
  simResults.value = d.value?.results ?? []
}
</script>
