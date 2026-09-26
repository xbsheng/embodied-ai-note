/// <reference types="vitepress/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 百度统计的全局队列
interface Window {
  _hmt?: unknown[][]
}
