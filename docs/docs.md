# 关于文档

当前文档使用[VitePress](https://vitepress.dev/)构建

为了编写文档，你可能需要准备[Nodejs](https://nodejs.org/)和[pnpm](https://pnpm.io/)

## 安装环境

### 安装Node.js

前往[Nodejs官网](https://nodejs.org/)下载安装包，安装完成后，打开命令行工具，输入 `node -v` 和 `npm -v` 检查是否安装成功

### 安装pnpm

安装完Nodejs后

执行

```bash
npm install -g pnpm
```

## 安装文档

先切换到 `docs` 目录

```bash
cd docs
```

安装依赖

```bash
pnpm install
```

### 预览文档

执行

```bash
npm run docs:dev
```

实时预览文档

现在修改md文件试试！

### 构建文档

你需要部署文档？

执行

```bash
npm run docs:build
```

将会在 `docs/.vitepress/dist` 目录下生成静态文件
