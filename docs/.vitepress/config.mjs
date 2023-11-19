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
