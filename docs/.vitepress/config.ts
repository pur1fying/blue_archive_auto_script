import { defineConfig } from 'vitepress'
import { fileURLToPath } from 'node:url'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Blue Archive Auto Script",
  description: "用于实现蔚蓝档案自动化",
  // NOTE: 默认情况下，我们假设站点将部署在域的根路径（/）。
  // 如果你的网站将在子路径上提供服务，例如 https://mywebsite.com/blog/，
  // 那么你需要在 VitePress 配置中将 base 选项设置为 /blog/。
  // 例如，如果你使用的是 GitHub（或 GitLab）页面，并部署到 user.github.io/repo/，
  // 则需要将你的 base 设置为 /repo/。
  base: '/',

  // 忽略死链接，因为我们的文档可能包含未完成的链接，
  // 这些链接可能会在将来的更新中修复。
  ignoreDeadLinks: true,

  vite: {
    resolve: {
      alias: [
        {
          find: /^.*\/VPDocOutlineItem\.vue$/,
          replacement: fileURLToPath(
            new URL('./components/VPDocOutlineItem.vue', import.meta.url)
          )
        },
      ]
    },
  },

  // 添加favicon
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: 'assets/logo.png' }],
    ['meta', { name: 'author', content: 'pur1fying' }],
  ],

  themeConfig: {
    outline: [2, 3],
    outlineTitle: '大纲',
    logo: '/assets/logo.png',
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '主页', link: '/' },
      { text: '下载', link: '/usage_doc/downloads'}
    ],
    search: {
      provider: 'local'
    },
    sidebar: {
      '/usage_doc/': [
        {
          text: '用户文档',
          items: [
            {text: '特性', link: '/usage_doc/features'},
            {text: '下载', link: '/usage_doc/downloads'},
            {text: '安装教程', link: '/usage_doc/install/choose_platform'},
            {text: '安装配置', link: '/usage_doc/install/setup_config'},
            {text: '配置', link: '/usage_doc/config'},
            {text: '活动相关', link: '/usage_doc/activity'},
            {text: '常见问题', link: '/usage_doc/faq'},
            {text: '上报问题', link: '/usage_doc/report'},
            {text: 'CLI用法', link: '/usage_doc/CLI'},
            {text: '卸载', link: '/usage_doc/uninstall'},
            {text: 'QQ群规定', link: '/usage_doc/qq_group_regulation'},
            {text: '项目破坏者', link: '/usage_doc/destroyer'}
          ]
        }
      ],
      '/develop_doc/': [
        {
          text: '开发文档',
            items: [
                {text: '总览', link: '/develop_doc/develop_guide'},
                {text: '开发环境', link: '/develop_doc/env'},
                {text: '模拟器连接', link: '/develop_doc/script/Connection'},
                {text: '模拟器截图', link: '/develop_doc/script/screenshot'},
                {text: '模拟器控制', link: '/develop_doc/script/control'},
                {text: '图像资源', link: '/develop_doc/script/image_resource'},
                {text: '图像识别', link: '/develop_doc/script/game_feature'},
                {text: '目标检测(YOLO)', link: '/develop_doc/script/baas_yolo_detection'},
                {text: '文字识别', link: '/develop_doc/script/ocr'},
                {text: 'Baas_thread', link: '/develop_doc/script/Baas_thread'},
                {text: '活动', link: '/develop_doc/script/activity'},
                {text: '自动战斗', link: '/develop_doc/script/auto_fight'},
                {text: '编写文档', link: '/develop_doc/docs'},
                {text: '模拟器开关/状态检测', link: '/develop_doc/script/emulator_manager'},
                {text: '配置详解', link: '/develop_doc/script/config'},
                {text: 'ConfigSet', link: '/develop_doc/script/ConfigSet'},
                {text: '开发约定', link: '/develop_doc/develop_format'},
                {text: '日志', link: '/develop_doc/log'},
                {text: 'C++代码', link: '/develop_doc/script/BAAS_Cpp'},
            ]
        }
      ]
    },
    socialLinks: [
      {
          icon: 'github',
          link: 'https://github.com/pur1fying/blue_archive_auto_script'
      },
      {
        icon: {
            svg: '<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg t="1749181158809" class="icon" viewBox="0 0 1092 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1997" xmlns:xlink="http://www.w3.org/1999/xlink" width="213.28125" height="200"><path d="M521.007 0L0 859.065 260.504 1024l53.99-184.999 413.375-31.18 107.266 204.805 256.673-153.56L521.008 0zM414.7 642.136l98.648-217.36 111.096 217.36H414.699z" fill="#EA5A60" p-id="1998"></path></svg>'
        },
        link: 'https://www.acfun.cn/u/76873903'
      }
    ],

    lastUpdated: {
      text: '更新于',
      formatOptions: {
        dateStyle: 'full',
        timeStyle: 'medium'
      }
    }
  }
})
