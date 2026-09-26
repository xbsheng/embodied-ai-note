<script setup>
import { watch } from 'vue'
import { useRoute } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import Giscus from './Giscus.vue'

const { Layout } = DefaultTheme

// 百度统计：首屏 PV 由注入的脚本自动上报，这里只补 SPA 路由切换
const route = useRoute()
let tracked = route.path
watch(
  () => route.path,
  (to) => {
    if (to === tracked) return
    tracked = to
    window._hmt?.push(['_trackPageview', to])
  },
)
</script>

<template>
  <Layout>
    <template #doc-after>
      <Giscus />
    </template>
  </Layout>
</template>
