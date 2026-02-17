
# 🏗️ フロントエンド開発ガイド

このドキュメントでは、**BAASデスクトップアプリケーション**の構造、
クライアントモジュールとバックエンド間のデータフロー、
および拡張時の運用設計を説明します。
対象読者は、**新機能の実装やシステム保守を担当するエンジニアチーム**です。

---

## 🧩 アプリケーション構成

Reactアプリは `App.tsx` でレンダリングされ、
**ThemeProvider**、**AppProvider**、および永続レイアウト枠（`MainLayout`）が統合されています。
軽量な **framer-motionルーター** によりページ切替時も状態を保持します。

* **エントリーポイント：** `main.tsx` — i18nとテーマ初期化後に `<App />` を描画。
* **プロバイダー：** `AppProvider` — UI設定、WebSocket接続、プロファイル一覧を管理。
* **レイアウト：** `MainLayout` — サイドバー (`Sidebar.tsx`) とヘッダー (`Header.tsx`) を保持。

---

## 🧱 主要モジュール

| モジュール               | 役割                                                       | 主なファイル                                      |
| :------------------ | :------------------------------------------------------- | :------------------------------------------ |
| **Context**         | UI設定・アクティブプロファイル共有                                       | `contexts/AppContext.tsx`                   |
| **State Stores**    | Zustandによりリモート状態を正規化                                     | `store/websocketStore.ts`                   |
| **Remote Services** | バックエンドとの暗号通信／ホットキー設定保持                                   | `services/hotkeyService.ts`                 |
| **Pages**           | `Home`・`Scheduler`・`Configuration`・`Settings`・`Wiki` ページ | `pages/*.tsx`                               |
| **Feature Forms**   | 各機能設定パネル（DynamicConfigに基づく）                              | `features/*Config.tsx`                      |
| **Shared UI**       | 入力、モーダル、ログなど共通コンポーネント群                                   | `components/ui`                             |
| **Hooks**           | ビジネスロジック用カスタムフック                                         | `hooks/useHotkeys.ts`, `hooks/useTheme.tsx` |

---

## 🔄 データフロー概要

### 🔌 WebSocket 初期化

1. `AppProvider` が起動時に `useWebSocketStore.getState().init()` を実行。
2. `init()` は順に **heartbeat**, **provider**, **sync** チャンネルを接続。
3. 接続完了後、設定マニフェストとライブイベントキューを取得。
4. Zustandのサブスクライバーが更新を受信。

---

### ⚙️ 設定更新サイクル

1. 設定フォームは `DynamicConfig` のローカルコピーを操作。
2. 保存時、変更差分をJSONパッチ形式で送信。
3. バックエンド確認後、`pendingCallbacks` がクリアされUI更新。
4. 新しい `config` メッセージによりローカル状態を同期。

---

### 📡 スケジューラーテレメトリ

* `Home` および `Scheduler` ページは `statusStore` と `logStore` を購読。
* ログは重複を排除して `globalLogStore` に反映。
* すべてのコマンドにはタイムスタンプが付与され、同期を容易に。

---

## ⚙️ 横断的関心事項

### 🌐 国際化（i18n）

翻訳は `assets/locales/*.json` に格納され、`react-i18next` によりロード。
既定言語は **中国語（zh）**、フォールバックは **英語**。

---

### ⚡ パフォーマンスとUX

* ページ保持により再マウントを防止。
* `useMemo` / `useCallback` により再描画最小化。
* スクロール領域は統一クラス `scroll-embedded` を使用。
* Zustandのバッチ更新で高頻度ログを効率的に処理。

---

### 🧰 使用技術

* **ビルド:** Vite + React 19 + TypeScript 5
* **スタイル:** Tailwind CSS + カスタムトークン
* **アニメーション:** framer-motion, ogl（粒子効果）

---

## 🚀 拡張手順チェックリスト

1. `features/` 内に新機能コンポーネントを作成し、`featureMap` に登録。
2. 翻訳辞書（`en.json`, `zh.json`）に新項目を追加。
3. `modify` / `patch` / `trigger` 経由で一貫した通信処理を実装。
4. UI設定項目は必要に応じて `AppContext` に公開。

---

この方針に従うことで：

* アプリケーションの**一貫性と拡張性**を保持。
* **キーボード操作**と**テレメトリ同期**が正確に機能。
* すべてのページ間で**WebSocket状態が整合的**に保たれます。
