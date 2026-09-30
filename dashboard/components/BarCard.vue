<template>
  <div class="rounded-lg bg-slate-900 p-4">
    <h3 class="text-sm font-semibold mb-3 text-slate-300">{{ title }}</h3>
    <div class="space-y-2">
      <div v-for="d in sorted" :key="d.key" class="flex items-center gap-2">
        <span class="w-24 truncate text-xs text-slate-400">{{ d.key }}</span>
        <div class="flex-1 h-4 bg-slate-800 rounded overflow-hidden">
          <div class="h-full bg-emerald-500 rounded" :style="{ width: pct(d.cnt) + '%' }"></div>
        </div>
        <span class="text-xs text-slate-400 w-20 text-right">{{ d.cnt.toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Dist { key: string; cnt: number }
const props = defineProps<{ title: string; data?: Dist[] | null }>()
const sorted = computed(() => (props.data ?? []).slice(0, 8))
const max = computed(() => Math.max(1, ...sorted.value.map((d) => d.cnt)))
function pct(c: number) { return Math.round((c / max.value) * 100) }
</script>
