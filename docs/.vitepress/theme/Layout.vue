<script setup>
import DefaultTheme from 'vitepress/theme'
import Giscus from './Giscus.vue'

const { Layout } = DefaultTheme
</script>

<template>
  <Layout>
    <template #doc-after>
      <Giscus />
    </template>
  </Layout>
</template>
