# 🏗️ Frontend Development Guide

This document describes how the **BAAS desktop application** is organised, how data flows between client modules and the backend, and the operational expectations when extending the platform.  
It targets **engineering and delivery teams** that need a canonical reference while onboarding or implementing new features.

---

## 🧩 Application Shell

The React application is rendered through `App.tsx`. It wires the **ThemeProvider**, **AppProvider**, and the persistent layout frame (`MainLayout`).  
Pages are swapped using a lightweight **framer-motion router** that keeps inactive pages mounted, allowing them to retain state while users change tabs.

- **Entry point:** `main.tsx` bootstraps i18n, theme, and renders `<App />`.
- **Providers:** `AppProvider` loads UI preferences, establishes WebSocket connectivity, injects the profile catalogue, and exposes setters via context.
- **Layout:** `MainLayout` contains the persistent sidebar (`Sidebar.tsx`) and header (`Header.tsx`).

---

## 🧱 Key Modules

| Module              | Responsibility                                                                              | Key Files                                                                   |
|:--------------------|:--------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------|
| **Context**         | Shares UI settings, active profile, and profile catalogue across the app.                   | `contexts/AppContext.tsx`                                                   |
| **State Stores**    | Zustand stores normalise remote state (config, events, status, logs) for components.        | `store/websocketStore.ts`, `store/globalLogStore.ts`                        |
| **Remote Services** | Encapsulate back-end contracts such as hotkey persistence and encrypted WebSocket sessions. | `services/hotkeyService.ts`, `lib/SecureWebSocket.ts`                       |
| **Pages**           | Route-level containers for `Home`, `Scheduler`, `Configuration`, `Settings`, and `Wiki`.    | `pages/*.tsx`                                                               |
| **Feature Forms**   | Modular configuration panels that operate on a slice of `DynamicConfig`.                    | `features/*Config.tsx`, `features/DailySweep.tsx`                           |
| **Shared UI**       | Reusable visual primitives and audience components (inputs, selectors, modals, loggers).    | `components/ui`, `components/AssetsDisplay.tsx`, `components/Particles.tsx` |
| **Hooks**           | Business logic hooks, including hotkey orchestration and theme handling.                    | `hooks/useHotkeys.ts`, `hooks/useTheme.tsx`                                 |

---

## 🔄 Data Flow Overview

### 🔌 WebSocket Initialisation

1. `AppProvider` calls `useWebSocketStore.getState().init()` during boot.
2. `init()` connects sequentially to **heartbeat**, **provider**, and **sync** channels using `SecureWebSocket`.
3. Once connected, the store pulls static data, configuration manifests, and live event queues.
4. Store setters broadcast updates to subscribed components via Zustand selectors.

---

### ⚙️ Configuration Update Cycle

1. Feature forms operate on a local draft copy of `DynamicConfig`.
2. On save, the form generates a minimal `patch` object and invokes `modify(path, patch, showToast)`.
3. The store emits a `sync` command with JSON patch semantics and registers a callback on `pendingCallbacks`.
4. When the backend acknowledges the command, the callback clears the pending state and optionally displays a toast via `sonner`.
5. Incoming `config` messages reconcile the local store so all subscribers refresh automatically.

---

### 📡 Scheduler Telemetry

- **Home** and **Scheduler** pages subscribe to `statusStore` and `logStore` to present runtime metrics.
- The log pipeline deduplicates entries and mirrors global logs into `globalLogStore` for the loading screen terminal.
- All outgoing commands (start/stop triggers, patches) are timestamped to simplify reconciliation.

---

## ⚙️ Cross-Cutting Concerns

### 🌐 Internationalisation

Translations are stored in `assets/locales/*.json` and loaded via `react-i18next`.  
The default language is **Chinese (`zh`)**, with **English fallback**.  
UI copy is organised by domain (scheduler, artifact, etc.) to simplify localisation updates.

---

### ⚡ Performance & UX

- **Mount preservation** (see `App.tsx`) prevents expensive components from reinitialising on tab changes.
- Feature forms apply `useMemo` and `useCallback` to prevent unnecessary re-renders.
- Scrolling areas use `scroll-embedded` utility classes for consistent styling.
- Real-time updates rely on **batched Zustand setters**; heavy updates (e.g., logs) append immutably to reduce reference churn.

---

### 🧰 Tooling

- **Build:** Vite + React 19 + TypeScript 5
- **Styling:** Tailwind CSS with custom tokens and reusable UI components
- **Animations:** `framer-motion` for transitions and `ogl` for particle effects

---

## 🚀 Extensibility Checklist

1. Create or update a feature component under `features/` and wire it into `featureMap` (Configuration page).
2. Expand translation dictionaries with new labels in both `en.json` and `zh.json`.
3. Persist server communication through `modify`, `patch`, or `trigger` to maintain consistent acknowledgement handling.
4. Expose UI settings via `AppContext` if they should be user-configurable.

---

Following this contract ensures that:

- The application remains **consistent and extensible**.
- **Keyboard navigation** and **telemetry synchronisation** function correctly.
- **WebSocket state** stays coherent across all pages.

---
