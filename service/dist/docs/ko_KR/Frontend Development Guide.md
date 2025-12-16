
# 🏗️ 프런트엔드 개발 가이드

이 문서는 **BAAS 데스크탑 애플리케이션**의 구조, 클라이언트 모듈과 백엔드 간 데이터 흐름,
그리고 플랫폼 기능 확장 시 기대 동작을 설명합니다.
엔지니어링 및 배포 팀이 온보딩하거나 기능을 구현할 때 참조할 수 있는 기준 문서입니다.

---

## 🧩 애플리케이션 셸 구조

React 앱은 `App.tsx`를 통해 렌더링됩니다.
이곳에서 **ThemeProvider**, **AppProvider**, 지속 레이아웃 프레임(`MainLayout`)이 연결됩니다.
사용자는 가벼운 **framer-motion 라우터**를 통해 페이지를 전환하며,
비활성 페이지도 상태를 유지하면서 탭을 전환할 수 있습니다.

* **진입점:** `main.tsx` — i18n, 테마를 초기화하고 `<App />`을 렌더링
* **Providers:** `AppProvider`는 UI 설정 로드, WebSocket 연결 설정, 프로필 카탈로그 주입,
  그리고 context를 통한 설정자(setter)를 노출
* **레이아웃:** `MainLayout`은 지속되는 사이드바(`Sidebar.tsx`)와 헤더(`Header.tsx`)를 포함

---

## 🧱 주요 모듈

| 모듈명                 | 책임 범위                                                                   | 주요 파일 경로                                                                    |
| :------------------ | :---------------------------------------------------------------------- | :-------------------------------------------------------------------------- |
| **Context**         | UI 설정, 활성 프로필, 프로필 카탈로그를 앱 전반에 공유                                       | `contexts/AppContext.tsx`                                                   |
| **State Stores**    | Zustand 상태 저장소가 원격 상태(config, 이벤트, 상태, 로그)을 정규화                         | `store/websocketStore.ts`, `store/globalLogStore.ts`                        |
| **Remote Services** | 핫키 지속성, 암호화된 WebSocket 세션 등 백엔드 계약을 캡슐화                                 | `services/hotkeyService.ts`, `lib/SecureWebSocket.ts`                       |
| **Pages**           | `Home`, `Scheduler`, `Configuration`, `Settings`, `Wiki` 등의 페이지 레벨 컨테이너 | `pages/*.tsx`                                                               |
| **Feature Forms**   | `DynamicConfig`의 일부를 다루는 구성 패널 모듈                                       | `features/*Config.tsx`, `features/DailySweep.tsx`                           |
| **Shared UI**       | 재사용 가능한 시각 요소 및 구성 요소 (입력, 선택기, 모달, 로거 등)                               | `components/ui`, `components/AssetsDisplay.tsx`, `components/Particles.tsx` |
| **Hooks**           | 비즈니스 로직 훅, 핫키 조율, 테마 처리 포함                                              | `hooks/useHotkeys.ts`, `hooks/useTheme.tsx`                                 |

---

## 🔄 데이터 흐름 개요

### 🔌 WebSocket 초기화

1. `AppProvider`는 부팅 시 `useWebSocketStore.getState().init()`을 호출
2. `init()`는 순차적으로 **heartbeat**, **provider**, **sync** 채널에 `SecureWebSocket`으로 연결
3. 연결되면, 스토어는 정적 데이터, 구성 매니페스트, 실시간 이벤트 큐를 가져옴
4. 스토어의 설정자(setter)는 Zustand 선택자를 통해 구독 컴포넌트에 업데이트를 방송

---

### ⚙️ 구성 업데이트 사이클

1. 기능 폼(form)은 `DynamicConfig`의 로컬 드래프트 복사본 위에서 작동
2. 저장 시, 폼은 최소 `patch` 객체를 생성하고 `modify(path, patch, showToast)`를 호출
3. 스토어는 JSON patch 방식의 `sync` 명령을 발행하고,
   `pendingCallbacks`에 콜백을 등록
4. 백엔드가 명령을 확인하면 콜백은 대기 상태를 해제하고,
   선택적으로 `sonner`로 토스트 알림을 표시
5. 수신된 `config` 메시지는 로컬 스토어를 조정해 모든 구독자가 자동으로 새로 고침됨

---

### 📡 스케줄러 텔레메트리

* **Home** 및 **Scheduler** 페이지는 `statusStore` 및 `logStore`를 구독해 런타임 지표를 제공합니다
* 로그 파이프라인은 중복 항목을 제거하고, 전역 로그를 `globalLogStore`에 미러링해 로딩 화면 터미널에 반영
* 모든 발신 명령(start/stop triggers, patches 등)은 타임스탬프가 붙어 조정 및 동기화가 쉬워집니다

---

## ⚙️ 범용 고려사항

### 🌐 국제화(i18n)

번역은 `assets/locales/*.json`에 저장되며 `react-i18next`를 통해 로드됩니다.
기본 언어는 **중국어 (`zh`)**, 보조 언어는 **영어**입니다.
UI 문구는 도메인별로 정리되어 있어 로컬라이제이션 업데이트가 간편합니다.

---

### ⚡ 성능 및 사용자 경험 (UX)

* **마운트 보존** 기능(예: `App.tsx`)은 탭 변경 시 비싼 컴포넌트 재초기화를 방지
* 기능 폼은 `useMemo`, `useCallback`을 적용해 불필요한 리렌더링 최소화
* 스크롤 구역은 `scroll-embedded` 유틸리티 클래스를 사용해 일관된 스타일 유지
* 실시간 업데이트는 **배치된 Zustand 설정자**를 사용하며,
  로그 같은 대량 업데이트는 참조 변경을 줄이기 위해 비가변 방식으로 추가

---

### 🧰 도구 구성

* **빌드:** Vite + React 19 + TypeScript 5
* **스타일링:** Tailwind CSS + 커스텀 토큰 + 재사용 UI 컴포넌트
* **애니메이션:** `framer-motion` for 전환, `ogl` for 파티클 효과

---

## 🚀 확장성 체크리스트

1. `features/` 아래에 기능 컴포넌트를 새로 만들거나 업데이트하고,
   `featureMap`에 연결
2. `en.json` 및 `zh.json` 양쪽에 새로운 레이블에 대한 번역 사전에 항목 추가
3. `modify`, `patch`, `trigger`를 통해 서버 통신을 유지해 일관된 확인 처리
4. 사용자 설정 가능해야 할 UI 설정은 `AppContext`를 통해 노출

---

이를 따르면:

* 애플리케이션은 **일관성과 확장성**을 유지
* **키보드 네비게이션** 및 **텔레메트리 동기화**가 정상 작동
* **WebSocket 상태**가 모든 페이지에 걸쳐 일관되게 유지됨
