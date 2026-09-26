<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vitepress'

const route = useRoute()
const container = ref(null)

// 参数来自 giscus.app 生成的配置
const attrs = {
  src: 'https://giscus.app/client.js',
  'data-repo': 'xbsheng/embodied-ai-note',
  'data-repo-id': 'R_kgDOUsSY0A',
  'data-category': 'Announcements',
  'data-category-id': 'DIC_kwDOUsSY0M4DGa8r',
  'data-mapping': 'pathname',
  'data-strict': '0',
  'data-reactions-enabled': '1',
  'data-emit-metadata': '0',
  'data-input-position': 'top',
  'data-theme': 'preferred_color_scheme',
  'data-lang': 'zh-CN',
  'data-loading': 'lazy',
  crossorigin: 'anonymous',
  async: '',
}

// VitePress 是 SPA，路由切换后要重新挂载，giscus 才会加载对应页面的评论
function mount() {
  if (!container.value) return
  container.value.innerHTML = ''
  const script = document.createElement('script')
  for (const [key, value] of Object.entries(attrs)) {
    script.setAttribute(key, value)
  }
  container.value.appendChild(script)
}

onMounted(mount)
watch(() => route.path, mount)
onUnmounted(() => {
  if (container.value) container.value.innerHTML = ''
})
</script>

<template>
  <div ref="container" class="giscus-container" />
</template>

<style scoped>
.giscus-container {
  margin-top: 32px;
}
</style>
