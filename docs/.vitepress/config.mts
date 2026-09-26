import { defineConfig } from 'vitepress'

// 中文按字切分 + 英文/数字按词切分，让本地搜索能命中中文关键词
function tokenize(text: string): string[] {
  const out: string[] = []
  const re = /[\u4e00-\u9fff]+|[A-Za-z0-9_.]+/g
  let m: RegExpExecArray | null
  while ((m = re.exec(text))) {
    const w = m[0]
    if (/[\u4e00-\u9fff]/.test(w)) {
      for (let i = 0; i < w.length; i++) out.push(w[i])
    } else {
      out.push(w.toLowerCase())
    }
  }
  return out
}

type Topic = { text: string; base: string; chapters: [string, string][] }

// 新增笔记主题时，在 topics 里加一条，章节目录随之自动生成
const topics: Topic[] = [
  {
    text: 'ROS2 笔记',
    base: '/ros2',
    chapters: [
      ['01-ros-history', 'ROS 发展史'],
      ['02-ros-setup', 'ROS 环境搭建'],
      ['03-ros-basics', 'ROS 开发入门'],
      ['04-ros-topic', 'ROS2 Topic 通讯'],
      ['05-ros-vision', 'ROS 视觉与控制'],
      ['06-ros-voice-ai', 'ROS 语音 & AI 与控制'],
    ],
  },
]

function topicSidebar({ text, base, chapters }: Topic) {
  return {
    text,
    items: chapters.map(([dir, title]) => ({
      // 目录名已带编号（01-xxx），直接用前缀当章节号，标题与 URL 不会再对不上
      text: `${dir.slice(0, 2)} · ${title}`,
      link: `${base}/${dir}/`,
    })),
  }
}

// GitHub Pages 项目站点通过 DOCS_BASE 传入子路径，例如 /ros2-notes/
const base = process.env.DOCS_BASE || '/'

export default defineConfig({
  base,
  lang: 'zh-CN',
  title: '具身智能学习笔记',
  description: 'ROS2 与具身智能的图文笔记 —— 可检索、可离线阅读',
  cleanUrls: true,
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: `${base}favicon.png` }],
    ['meta', { name: 'theme-color', content: '#023272' }],
  ],

  markdown: {
    lineNumbers: true,
    image: { lazyLoading: true },
  },

  themeConfig: {
    logo: '/logo.png',
    siteTitle: '具身智能学习笔记',
    nav: topics.map((t) => ({
      text: t.text,
      link: `${t.base}/${t.chapters[0][0]}/`,
      activeMatch: `^${t.base}/`,
    })),
    sidebar: topics.map(topicSidebar),
    socialLinks: [
      { icon: 'github', link: 'https://github.com/xbsheng/embodied-ai-note' },
    ],
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    editLink: {
      pattern:
        'https://github.com/xbsheng/embodied-ai-note/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页面',
    },
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色',
    darkModeSwitchTitle: '切换到深色',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    lastUpdated: {
      text: '更新于',
      formatOptions: { dateStyle: 'short', timeStyle: 'short' },
    },
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清除',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
        miniSearch: {
          options: { tokenize },
          searchOptions: { prefix: true, fuzzy: 0.2, combineWith: 'AND' },
        },
      },
    },
    footer: {
      message: '具身智能学习笔记，仅供学习使用',
      copyright: '原始课件版权归原作者所有',
    },
  },
})
