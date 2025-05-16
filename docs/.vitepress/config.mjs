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
    outline: [2, 3],
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
            {text: '下载', link: '/usage_doc/downloads'},
            {text: '安装教程', link: '/usage_doc/install/choose_platform'},
            {text: '自定义安装', link: '/usage_doc/install/setup_config'},
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
      { icon: 'github', link: 'https://github.com/pur1fying/blue_archive_auto_script' },
      { icon: {
          svg: '<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg t="1736747975896" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="4257" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="200"><path d="M769.856 348.928H261.248a27.84 27.84 0 0 0-28.48 27.584v337.152a27.712 27.712 0 0 0 28.48 27.456h508.608a26.496 26.496 0 0 0 27.072-27.456V376.512a26.688 26.688 0 0 0-27.072-27.584zM295.872 473.536l143.36-27.456 10.816 53.76-141.888 27.456zM516.8 637.44c-44.032 48-90.24-15.168-90.24-15.168l23.488-15.168s31.424 56.704 66.432-18.432c33.6 72.96 70.784 19.2 70.784 19.2l21.312 13.696s-39.68 63.872-91.712 15.872z m212.672-110.144L587.2 499.84l11.2-53.824 142.976 27.456z" fill="#53D4F4" p-id="4258"></path><path d="M512 0a512 512 0 1 0 512 512 512 512 0 0 0-512-512z m269.632 809.408a462.4 462.4 0 0 0-47.872 0s-2.624 41.088-37.696 41.792a39.552 39.552 0 0 1-41.792-39.552c-21.44 0-279.552 1.152-279.552 1.152s-4.544 38.08-39.552 38.08a39.68 39.68 0 0 1-39.552-38.08c-22.976 0-53.888-0.768-53.888-0.768a123.52 123.52 0 0 1-87.808-117.184c1.152-100.992 0-300.8 0-300.8a117.376 117.376 0 0 1 85.504-119.808 5388.8 5388.8 0 0 1 161.984-1.536l-65.92-64s-10.176-12.8 7.168-27.136 18.432-8.512 24.512-4.352 98.304 95.104 98.304 95.104h-12.416c35.392 0 71.936 0.576 107.008 0.576 13.568-13.568 90.816-89.216 96-92.928s7.168-10.112 24.512 4.16 7.168 27.136 7.168 27.136l-64.448 62.144c88.512 0.768 156.736 1.152 156.736 1.152a120.896 120.896 0 0 1 89.6 119.424c-1.152 100.224 0.384 301.76 0.384 301.76s-4.864 97.92-88.512 113.408z" fill="#53D4F4" p-id="4259"></path></svg>'
        },
        link: 'https://space.bilibili.com/496075546'
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
