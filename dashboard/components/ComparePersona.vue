<template>
  <section class="p-6">
    <h2 class="text-lg font-semibold mb-3">집단 비교</h2>
    <p class="text-sm text-slate-400 mb-4">두 집단을 구조화 조건으로 비교합니다 (MCP 경유).</p>

    <!-- 두 그룹 입력 -->
    <div class="grid md:grid-cols-2 gap-4 mb-4">
      <div class="rounded-lg bg-slate-900 border border-slate-800 p-4">
        <div class="text-sm font-semibold text-emerald-400 mb-2">그룹 A</div>
        <div class="space-y-2">
          <input v-model="a.label" placeholder="라벨 (예: 서울 30대 여성 1인가구)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
          <div class="grid grid-cols-2 gap-2">
            <input v-model="a.province" placeholder="시도" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
            <input v-model="a.sex" placeholder="성별 (여자/남자)" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
            <input v-model="a.age_min" placeholder="최소 연령" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
            <input v-model="a.age_max" placeholder="최대 연령" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
          </div>
          <input v-model="a.family_type" placeholder="가구 (예: 혼자 거주)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
        </div>
      </div>

      <div class="rounded-lg bg-slate-900 border border-slate-800 p-4">
        <div class="text-sm font-semibold text-sky-400 mb-2">그룹 B</div>
        <div class="space-y-2">
          <input v-model="b.label" placeholder="라벨 (예: 경기 40대 여성 자녀가구)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
          <div class="grid grid-cols-2 gap-2">
            <input v-model="b.province" placeholder="시도" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
            <input v-model="b.sex" placeholder="성별 (여자/남자)" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
            <input v-model="b.age_min" placeholder="최소 연령" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
            <input v-model="b.age_max" placeholder="최대 연령" class="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
          </div>
          <input v-model="b.family_type" placeholder="가구 (예: 배우자·자녀와 거주)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm" />
        </div>
      </div>
    </div>

    <div class="flex gap-2 mb-4">
      <button @click="compare" class="bg-emerald-600 hover:bg-emerald-500 rounded px-4 py-2 text-sm font-semibold">
        {{ loading ? '비교 중...' : '비교' }}
      </button>
    </div>

    <!-- 오류 -->
    <div v-if="error" class="mb-4 p-3 rounded bg-red-900/50 text-red-300 text-sm">{{ error }}</div>

    <!-- 결과 -->
    <div v-if="result" class="space-y-4">
      <!-- 인구 요약 -->
      <div class="grid grid-cols-2 gap-4">
        <div class="rounded-lg bg-slate-900 border border-slate-800 p-4">
          <div class="text-xs text-slate-400">{{ result.group_a?.label }}</div>
          <div class="text-2xl font-bold text-emerald-400">{{ result.group_a?.population?.toLocaleString() }}명</div>
          <div class="text-xs text-slate-500">비중 {{ (result.group_a?.population_ratio * 100)?.toFixed(1) }}%</div>
        </div>
        <div class="rounded-lg bg-slate-900 border border-slate-800 p-4">
          <div class="text-xs text-slate-400">{{ result.group_b?.label }}</div>
          <div class="text-2xl font-bold text-sky-400">{{ result.group_b?.population?.toLocaleString() }}명</div>
          <div class="text-xs text-slate-500">비중 {{ (result.group_b?.population_ratio * 100)?.toFixed(1) }}%</div>
        </div>
      </div>

      <!-- 차이 항목들 -->
      <div v-for="dim in dims" :key="dim.key" class="rounded-lg bg-slate-900 border border-slate-800 p-4">
        <div class="text-sm font-semibold text-slate-300 mb-2">{{ dim.label }}</div>
        <div v-if="diffList(dim.key).length === 0" class="text-xs text-slate-500">유의미한 차이 없음</div>
        <div v-else class="space-y-2">
          <div v-for="d in diffList(dim.key)" :key="d.key" class="flex items-center gap-2">
            <span class="w-32 truncate text-xs text-slate-400">{{ d.key }}</span>
            <!-- A 막대 -->
            <div class="flex-1 flex items-center gap-1">
              <span class="text-xs text-emerald-400 w-10 text-right">{{ (d.group_a_ratio * 100).toFixed(1) }}%</span>
              <div class="flex-1 h-4 bg-slate-800 rounded overflow-hidden">
                <div class="h-full bg-emerald-500 rounded" :style="{ width: pct(d.group_a_ratio) + '%' }"></div>
              </div>
            </div>
            <!-- B 막대 -->
            <div class="flex-1 flex items-center gap-1">
              <span class="text-xs text-sky-400 w-10 text-right">{{ (d.group_b_ratio * 100).toFixed(1) }}%</span>
              <div class="flex-1 h-4 bg-slate-800 rounded overflow-hidden">
                <div class="h-full bg-sky-500 rounded" :style="{ width: pct(d.group_b_ratio) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
const a = reactive({ label: '서울 30대 여성 1인가구', province: '서울', sex: '여자', age_min: '30', age_max: '39', family_type: '혼자 거주' })
const b = reactive({ label: '경기 40대 여성 자녀가구', province: '경기', sex: '여자', age_min: '40', age_max: '49', family_type: '배우자·자녀와 거주' })

const result = ref<any>(null)
const error = ref('')
const loading = ref(false)

const dims = [
  { key: 'occupation_diff', label: '직업 차이' },
  { key: 'family_type_diff', label: '가구 차이' },
  { key: 'housing_type_diff', label: '주거 차이' },
  { key: 'education_diff', label: '학력 차이' },
]

function diffList(key: string) {
  return result.value?.comparison?.[key] || []
}

function pct(ratio: number) {
  return Math.min(100, ratio * 100)
}

function clean(g: any) {
  const out: any = { label: g.label }
  if (g.province) out.province = g.province
  if (g.sex) out.sex = g.sex
  if (g.age_min) out.age_min = parseInt(g.age_min)
  if (g.age_max) out.age_max = parseInt(g.age_max)
  if (g.family_type) out.family_type = g.family_type
  return out
}

async function compare() {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await useFetch('/api/mcp/call', {
      method: 'POST',
      body: { toolName: 'compare_persona', args: { group_a: clean(a), group_b: clean(b) } },
    })
    if (data.value?.ok) {
      result.value = data.value.result
    } else {
      error.value = data.value?.error || '비교 실패'
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>
