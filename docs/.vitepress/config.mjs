import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Blue Archive Auto Script",
  description: "用于实现蔚蓝档案自动化",
  // NOTE: 默认情况下，我们假设站点将部署在域的根路径（/）。
  // 如果你的网站将在子路径上提供服务，例如 https://mywebsite.com/blog/，
  // 那么你需要在 VitePress 配置中将 base 选项设置为 /blog/。
  // 例如，如果你使用的是 GitHub（或 GitLab）页面，并部署到 user.github.io/repo/，
  // 则需要将你的 base 设置为 /repo/。
  base: '/blue_archive_auto_script/',

  // 忽略死链接，因为我们的文档可能包含未完成的链接，
  // 这些链接可能会在将来的更新中修复。
  ignoreDeadLinks: true,

  // 添加favicon
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: 'assets/logo.png' }],
    ['meta', { name: 'author', content: 'pur1fying' }],
  ],

  themeConfig: {
    logo: 'assets/logo.png',
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
            {text: '安装', link: '/usage_doc/install/choose_platform'},
            {text: '配置', link: '/usage_doc/config'},
            {text: '常见问题', link: '/usage_doc/faq'},
            {text: '上报问题', link: '/usage_doc/report'},
            {text: '编写文档', link: '/usage_doc/docs'},
            {text: '已知问题', link: '/usage_doc/about'},
            {text: 'CLI用法', link: '/usage_doc/CLI'}
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
                {text: 'Baas_thread', link: '/develop_doc/script/Baas_thread'},
                {text: '模拟器开关/状态检测', link: '/develop_doc/script/device_operation'},
                {text: '配置详解', link: '/develop_doc/script/config'},
                {text: '开发约定', link: '/develop_doc/develop_format'}
            ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/pur1fying/blue_archive_auto_script' },
        { icon: 'assets/Bilibili.svg', link: 'https://space.bilibili.com/259089751/upload/opus' }
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
