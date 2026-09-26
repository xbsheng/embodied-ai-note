# 具身智能学习笔记

ROS2 与具身智能的图文笔记，用 [VitePress](https://vitepress.dev) 构建，支持中文全文搜索与离线阅读。

## 内容

| 章节 | 主题                 |
| ---- | -------------------- |
| 01   | ROS 发展史           |
| 02   | ROS 环境搭建         |
| 03   | ROS 开发入门         |
| 04   | ROS2 Topic 通讯      |
| 05   | ROS 视觉与控制       |
| 06   | ROS 语音 & AI 与控制 |

## 本地开发

```bash
pnpm install       # 安装依赖，并自动配置 git pre-commit 钩子
pnpm docs:dev      # 开发服务器
pnpm docs:build    # 构建到 docs/.vitepress/dist
pnpm docs:preview  # 预览构建产物

pnpm format        # Prettier 格式化
pnpm format:check  # 只检查，不改动
```

## 目录结构

```text
docs/
  .vitepress/config.mts    # 站点配置：导航、侧边栏、本地搜索分词
  public/                  # logo、favicon 等静态资源
  index.md                 # 首页
  ros2/<章节>/index.md     # 正文
  ros2/<章节>/images/      # 该章配图（相对路径引用）
```

## 版权

- 笔记中部分内容摘自网络，**版权归原作者所有**，此处仅作学习交流。
- 欢迎引用，但请注明出处，请勿用于商业用途。
