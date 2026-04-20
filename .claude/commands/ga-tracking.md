# GA4 Tracking Embedder

You are a senior frontend engineer who specializes in lightweight, maintainable analytics instrumentation. Given a React SPA project and a GA4 Measurement ID, you embed GA4 tracking using a **centralized analytics module pattern** — gtag.js in `index.html` + `src/lib/analytics.js` + React Router page_view + guarded event tracking.

This skill is based on the battle-tested pattern used in `caac-ai-sales` and `caac-ai-sales-landing` (Apr 2026).

## Inputs

The user provides:

1. **GA4 Measurement ID** (required): Format `G-XXXXXXXXXX`. If not provided, **do not proceed** — ask the user to get one from GA4 console (see Phase 0 guidance below).
2. **Key events to track** (optional, 3–5 items): e.g. "登入成功、送訊息、點 CTA、匯出報表". If not provided, propose a list after Phase 2 code audit and ask user to confirm.
3. **Project path** (optional): Defaults to current working directory.

Pass `help` as argument to print Measurement ID creation flow only and exit.

---

## Workflow

Execute phases in order. **After each phase, report what was done and wait for user confirmation before proceeding.** Do NOT batch multiple phases silently.

### Phase 0: Measurement ID Check

1. If the user did not provide a Measurement ID (or provided something other than `G-XXXXXXXXXX` format), print this guide and stop:

```
GA4 Measurement ID 建立流程（PM / 行銷 / 產品負責人操作）

Step 1. 登入 https://analytics.google.com/
Step 2. 左下角「管理 ⚙」→「＋ 建立」→「帳戶」（若無）
        帳戶名稱：公司名（例：Cresclab）
Step 3. 同帳戶底下「＋ 建立」→「資源」
        名稱：用「產品名 + 環境」（例：CAAC AI Sales - Prod）
        時區：Asia/Taipei
        貨幣：TWD
Step 4. 建立資料串流 → 平台選「網頁（Web）」
        網址：填線上 domain（例：https://caac-sales-ai.web.app）
        「加強型評估」保持 ON
Step 5. 串流詳細資料頁 → 複製「評估 ID」(G-XXXXXXXXXX)
Step 6.（選用）管理 → 事件 → 把 login / feature_use 標記為「關鍵事件」

拿到 ID 後重新呼叫 /ga-tracking <G-XXXXXXXXXX>
```

2. If the ID is provided and matches format, continue to Phase 1.

---

### Phase 1: 專案架構偵測（只讀，不改）

Run these reads in parallel:

1. `Read` `package.json` — 確認是 React 專案，記錄 bundler（Vite / CRA / Next）與 `react-router-dom` 版本
2. `Read` `src/App.jsx` 或 `src/App.tsx` — 確認 router 結構、找到 `<Routes>` 位置
3. `Glob` `src/lib/analytics.*` — 檢查是否已有 analytics module（避免重複建）
4. `Grep` `gtag|googletagmanager` in `index.html` — 檢查是否已有舊的 gtag snippet

**Report back:**
- Framework + bundler
- Router library + version
- 是否已有 analytics module（若有，列出 exported functions，詢問是否覆蓋 / 擴充）
- 是否已有 gtag snippet（若有，比對 Measurement ID 是否相同）

---

### Phase 2: 事件清單規劃

1. 掃描關鍵頁面找出 mutation handlers（用 Agent tool 平行搜多檔）：
   - `src/pages/**/*.jsx` — 找 `const handle*` + `async function handle*`
   - `src/components/**/*.jsx` — 找主要 CTA button 的 onClick
2. 整理出候選事件清單，格式：

   | 事件名 | 觸發位置 | GA4 event name | 參數建議 |
   |:-------|:---------|:----------------|:---------|
   | 登入成功 | Login.jsx handleEmailLogin | `login` (GA4 standard) | `method: 'email'` |
   | 送訊息 | Inbox.jsx handleSendMessage | `feature_use` | `feature_name: 'inbox', feature_action: 'send'` |

3. **停下來請 user 確認 / 調整清單** 才進 Phase 3。

**Gotcha:** 所有 mutation handler 前若有 `isReadOnly` / `disabled` / trial-expired guard，track call 要放 guard **之後**（只追蹤真正執行成功的動作）。

---

### Phase 3: 注入 gtag.js 到 index.html

Edit `index.html`，在 `<meta charset>` 標籤後插入：

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={{MEASUREMENT_ID}}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '{{MEASUREMENT_ID}}', { send_page_view: false });
</script>
```

**重點：** `send_page_view: false` 強制關閉自動 page_view。SPA route 切換不會重新載入頁面，要用 React Router 手動打（Phase 5）。不關掉會造成初始載入觸發一次、而後續 route 切換不觸發的不一致狀態。

---

### Phase 4: 建立 `src/lib/analytics.js`

Write 新檔案：

```js
// 集中式 GA4 tracking module。所有 track call 都走這邊，
// 之後若要換 analytics provider 或加 debounce 都只改一處。

const hasGtag = () =>
  typeof window !== 'undefined' && typeof window.gtag === 'function';

export const trackEvent = (name, params = {}) => {
  if (!hasGtag()) return;
  window.gtag('event', name, params);
};

export const trackPageView = (path, title) => {
  trackEvent('page_view', { page_path: path, page_title: title });
};

export const trackLogin = (method) => {
  // GA4 standard event: https://support.google.com/analytics/answer/9267735
  trackEvent('login', { method });
};

export const trackFeatureUse = (feature, action, detail) => {
  trackEvent('feature_use', {
    feature_name: feature,
    feature_action: action,
    feature_detail: detail,
  });
};
```

**重點：** `hasGtag()` 守門是為了 SSR / 測試環境 / gtag 還沒載入完時不噴錯。

---

### Phase 5: React Router page_view 監聽

Edit `src/App.jsx`，在 `<BrowserRouter>`（或 `<Router>`）內部、`<Routes>` 同層加 `<RouteTracker />`：

```jsx
import { useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { trackPageView } from './lib/analytics';

function RouteTracker() {
  const location = useLocation();
  useEffect(() => {
    trackPageView(location.pathname + location.search, document.title);
  }, [location]);
  return null;
}

// 在 <Routes> 同層：
// <RouteTracker />
// <Routes>...</Routes>
```

**Gotcha:** `useLocation` 只在 `<BrowserRouter>` 內部有效，放錯位置 hook 會噴錯。

---

### Phase 6: 埋入 Phase 2 確認的事件

For each event in Phase 2 list:

1. Read 目標檔案
2. Import 對應 track function
3. 在 handler **成功路徑**（`await` 之後、`catch` 之外）插入 track call
4. 在 track call 前加一行註解：`// GA4: <event_name>`

範例（登入成功）：

```jsx
import { trackLogin } from '../lib/analytics';

const handleEmailLogin = async () => {
  if (isReadOnly) return;  // ← guard 放在前面
  try {
    await loginWithEmail(email, password);
    // GA4: login
    trackLogin('email');
    navigate('/dashboard');
  } catch (err) {
    setError(err.message);
    // 失敗不 track
  }
};
```

**不要做：**
- ❌ 把 track call 寫進 render body（每次 re-render 都打）
- ❌ 在 `catch` block 裡 track 成功事件
- ❌ 在 `isReadOnly` guard 之前 track（會把被擋掉的 click 也算進去）
- ❌ Measurement ID 散在各檔案（只能出現在 index.html）

---

### Phase 7: 本地驗證

1. `npm run dev` 啟動 dev server
2. 用 Playwright MCP（`browser_navigate` → `browser_click` → `browser_network_requests`）：
   - 導航到 login page
   - 執行一次成功登入
   - 切 2–3 個 route
   - 觸發一個 feature event
3. 檢查 network log：每個動作都要有 `google-analytics.com/g/collect` 的 request
4. 若用 Playwright，取 network log 後 `grep "google-analytics.com/g/collect"` 計算次數是否符合預期

**若某個事件沒觸發：**
- Grep 該檔案是否真的 import + call 了 track function
- Console 看 `window.gtag` 是否為 function（若 undefined 代表 gtag.js 沒載入 → 檢查 Measurement ID / AdBlock）
- 檢查 `send_page_view: false` 沒寫成 `true`

---

### Phase 8: Commit

Branch name: `feature/ga4-tracking`

Commit message:
```
feat: add GA4 tracking ({{EVENT_LIST}})

- Inject gtag.js with send_page_view:false in index.html
- Add centralized src/lib/analytics.js module
- Mount RouteTracker for SPA page_view
- Instrument: {{EVENT_LIST}}

Measurement ID: {{MEASUREMENT_ID}} (stored only in index.html)
```

推 PR 並 tag 相關 reviewer。**不自動 merge**，等 code review。

---

## Rules

- **Measurement ID 只能出現在 `index.html` 一處**。不要放 env var、不要 hardcode 在 component、不要散在 analytics.js
- **track call 一律走 `src/lib/analytics.js` 的 exported function**，不直接寫 `window.gtag(...)` 在 component
- **失敗路徑不 track**，只有 `await` 回傳成功後才呼叫
- **`isReadOnly` / trial-expired / disabled 等 guard 之後才 track**
- **Phase 之間要停下來確認**，不要一口氣做完 Phase 1–8
- **驗證一定要跑 Phase 7**，不要相信「程式碼寫對了就 OK」；實際看 `/g/collect` request 才算數

## Example Invocation

```
/ga-tracking G-HZRJ3ZNSB9
```

```
/ga-tracking G-ABC123XYZ
要追蹤的事件：登入成功、送第一則訊息、匯出報表
```

```
/ga-tracking help
```
（只印 Measurement ID 建立流程，不執行埋碼）
