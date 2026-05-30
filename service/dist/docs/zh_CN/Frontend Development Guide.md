
# 🏗️ 前端开发指南

本文档说明了 **BAAS 桌面端应用** 的整体架构、前后端数据流与扩展规范，
主要面向 **工程与交付团队**，用于新功能开发或项目接入参考。

---

## 🧩 应用壳（Application Shell）

React 应用由 `App.tsx` 渲染，负责加载 **ThemeProvider**、**AppProvider** 与主框架 `MainLayout`。
页面切换使用轻量级 **framer-motion 路由**，在切换标签页时保持非活动页挂载以保存状态。

* **入口文件：** `main.tsx` → 初始化 i18n、主题并渲染 `<App />`
* **Provider：** `AppProvider` 加载 UI 偏好、建立 WebSocket 连接、注入配置数据并通过 context 提供方法
* **布局：** `MainLayout` 含侧边栏 (`Sidebar.tsx`) 与顶部栏 (`Header.tsx`)

---

## 🧱 核心模块

| 模块                  | 功能说明                                                   | 关键文件                                                                      |
| :------------------ | :----------------------------------------------------- | :------------------------------------------------------------------------ |
| **Context**         | 在全局共享 UI 设置、当前档案及档案目录。                                 | `contexts/AppContext.tsx`                                                 |
| **State Stores**    | 使用 Zustand 管理远程状态（配置、事件、状态、日志等）。                       | `store/websocketStore.ts`、`store/globalLogStore.ts`                       |
| **Remote Services** | 封装后端接口，如快捷键持久化、加密 WebSocket 会话等。                       | `services/hotkeyService.ts`、`lib/SecureWebSocket.ts`                      |
| **Pages**           | 对应路由的页面容器（Home、Scheduler、Configuration、Settings、Wiki）。 | `pages/*.tsx`                                                             |
| **Feature Forms**   | 模块化配置面板，对应 `DynamicConfig` 的局部操作。                      | `features/*Config.tsx`、`features/DailySweep.tsx`                          |
| **Shared UI**       | 可复用的界面组件（输入框、选择器、模态框、日志面板等）。                           | `components/ui`、`components/AssetsDisplay.tsx`、`components/Particles.tsx` |
| **Hooks**           | 包含快捷键控制、主题切换等业务逻辑。                                     | `hooks/useHotkeys.ts`、`hooks/useTheme.tsx`                                |

---

## 🔄 数据流说明

### 🔌 WebSocket 初始化

1. 启动时由 `AppProvider` 调用 `useWebSocketStore.getState().init()`；
2. `init()` 依次连接 **heartbeat**、**provider**、**sync** 通道；
3. 建立连接后，拉取静态数据、配置清单及事件队列；
4. Zustand 将更新广播至订阅组件。

---

### ⚙️ 配置更新循环

1. 功能表单在本地维护 `DynamicConfig` 草稿；
2. 点击保存后生成最小 `patch`，并调用 `modify(path, patch, showToast)`；
3. Store 发送 `sync` 指令并注册回调；
4. 后端确认后，清除等待状态并可通过 `sonner` 弹窗提示；
5. 接收到新的 `config` 消息后，自动同步各组件。

---

### 📡 调度与监控

* 首页与调度页订阅 `statusStore` 与 `logStore` 展示运行数据；
* 日志流水去重后同步至全局日志；
* 所有外发命令均带时间戳以便回溯。

---

## ⚙️ 跨模块事项

### 🌐 国际化

翻译文件位于 `assets/locales/*.json`，使用 `react-i18next` 加载。
默认语言为 **中文（zh）**，英文为回退语言。

---

### ⚡ 性能与体验

* 组件挂载保持，避免频繁初始化；
* 使用 `useMemo`、`useCallback` 减少渲染；
* 滚动区域统一使用 `scroll-embedded`；
* 重日志更新采用不可变追加以减少引用变化。

---

### 🧰 工具栈

* **构建：** Vite + React 19 + TypeScript 5
* **样式：** Tailwind CSS
* **动画：** `framer-motion`、`ogl`

---

## 🚀 扩展流程清单

1. 在 `features/` 中创建或更新功能组件并加入 `featureMap`；
2. 更新 `en.json` 与 `zh.json` 翻译字段；
3. 使用 `modify/patch/trigger` 保持后端确认一致性；
4. 若新增用户设置，则在 `AppContext` 暴露接口。

---

遵守以上规范可确保：

* 应用结构一致且可扩展；
* 键盘导航与实时状态同步；
* WebSocket 状态在各页面保持一致。
