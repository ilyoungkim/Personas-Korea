<template>
  <div class="rounded bg-slate-900 border border-slate-800 p-3">
    <div class="flex items-center gap-2 mb-1">
      <span class="text-xs font-bold px-2 py-0.5 rounded" :class="methodClass">{{ method }}</span>
      <code class="text-xs text-slate-200 break-all">{{ path }}</code>
    </div>
    <div class="text-xs text-slate-500">{{ desc }}</div>
    <pre class="mt-2 text-xs text-slate-400 bg-slate-950 rounded p-2 overflow-auto">{{ example }}</pre>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ method: string; path: string; desc: string; example: string }>()

const methodClass = computed(() => {
  if (props.method === 'GET') return 'bg-emerald-600 text-white'
  if (props.method === 'POST') return 'bg-sky-600 text-white'
  return 'bg-slate-600 text-white'
})
</script>
