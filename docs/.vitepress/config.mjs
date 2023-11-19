import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Blue Archive Auto Script",
  description: "用于实现蔚蓝档案自动化",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '主页', link: '/' },
      { text: '下载', link: '/downloads' }
    ],

    sidebar: [
      {
        text: '文档',
        items: [
          { text: '特性', link: '/features' },
          { text: '安装', link: '/install' },
          { text: '配置', link: '/config' },
          { text: '常见问题', link: '/faq' },
          { text: '上报问题', link: '/report' },
          { text: '编写文档', link: '/docs' },
          { text: '关于', link: '/about' }
        ]
      },
      {
        text: 'Examples',
        items: [
          { text: 'Markdown Examples', link: '/markdown-examples' },
          { text: 'Runtime API Examples', link: '/api-examples' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/pur1fying/blue_archive_auto_script' }
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
