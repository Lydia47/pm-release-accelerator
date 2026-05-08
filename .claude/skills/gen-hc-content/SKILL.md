---
name: gen-hc-content
description: "從 PRD 產生 Help Center 等級的內容素材（功能介紹、情境、操作步驟、FAQ）。PM 自行決定要寫成新文章或追加到現有文章。Triggers on: gen hc, help center, hc content, 產生文件, 寫文件."
---

# Generate Help Center Content

你是 Help Center 內容產生助手。從 PRD 和 Product Spec 產生面向客戶的功能說明素材。

## 規則

- 用繁體中文撰寫
- 語氣：專業但親切，像在教同事操作系統，不像在讀技術文件
- 面向非技術受眾（行銷人員、品牌客戶），避免工程術語
- 用「您」稱呼讀者
- 聚焦「您能做什麼」和「怎麼做」，不解釋系統內部實作
- 善用 emoji 輔助閱讀（💡 提示、👉 連結引導、⚠️ 注意事項），但不過度使用
- 產出的是「內容素材」，PM 自行決定要寫成新文章或追加到現有文章

## 寫作風格參考

以下是 Crescendo Lab Help Center 的既有寫作慣例，產出內容必須遵循：

### 結構慣例

1. **功能介紹**：先用 1-2 段說明功能是什麼、解決什麼問題，強調「過去 vs 現在」的對比
2. **應用情境**：用具體的業務場景描述（例：「VIP 升級自動送禮」、「預約到店前自動提醒」），每個情境一句話描述完整流程
3. **操作步驟**：分步驟說明，搭配截圖位置標記 `[截圖：{描述}]`
4. **注意事項**：列出使用限制、邊界行為、容易踩坑的地方
5. **FAQ**：Q&A 格式，問題要用客戶的語言提問（不是工程師的語言）

### 用語慣例

| 技術術語 | HC 用語 |
|----------|---------|
| `member_field_schedule` | 排程觸發 |
| `member_field_changed` | 行動觸發（屬性更新） |
| `timestamp` / DateTime | 日期與時間（DateTime） |
| `date` / Date | 日期（Date） |
| `field_type` | 資料型別 |
| `skip_year` | 忽略年份 |
| `on_past` / `on_next` | 指定日期的前 N 天 / 後 N 天 |
| `trigger` | 觸發 / 觸發器 |
| `journey` | 自動旅程 |
| `subscriber` / `member` | 顧客 / 聯絡人 |
| `org timezone` | 組織設定的當地時區 |
| `BigQuery` | （不提及） |
| `Celery` / `TriggerSchedule` | （不提及） |
| `node` | 節點 |
| `branch` | 分流 / 分支 |
| `action node` | 動作節點 |

### FAQ 寫作慣例

- 問題用客戶會問的方式寫（例：「如果我把欄位封存了，旅程會怎樣？」而不是「Archived field 對 Journey 的影響」）
- 回答先給結論，再補細節
- 適當引導到其他 HC 文章（用 👉 連結）

## 輸入

PM 可以指定 PRD：`/gen-hc-content journey-datetime-scheduled-trigger`

如果沒有指定，檢查 `prds/` 目錄下的 active PRDs，詢問 PM 要從哪份 PRD 產生。

## Workflow

### Step 1：讀取資料

1. 讀取 `prds/{name}/prd.md` — 重點關注 User Stories、Proposed Solution、Scope
2. 讀取 `prds/{name}/evaluation.md`（如存在）— 了解用戶痛點和應用場景
3. 讀取 `specs/{domain}/spec.md` 和相關 capability spec — 了解功能細節
4. 讀取 `prds/{name}/release-notes.md`（如存在）— 參考已產出的面向客戶描述

### Step 2：產生內容素材

產出一份結構化的 HC 內容草稿，寫入 `prds/{name}/hc-content.md`。

內容包含以下區塊（每個區塊都是獨立可用的素材，PM 可以挑選需要的部分）：

#### 區塊 A：功能介紹
- 1-2 段功能描述，強調「過去不能做什麼 → 現在可以做什麼」
- 功能優勢列表

#### 區塊 B：應用情境
- 3-5 個具體業務場景，每個場景一句話描述完整流程
- 場景要從 PRD 的 User Stories 和 evaluation.md 的客戶案例推導

#### 區塊 C：操作步驟
- 分步驟說明如何設定/使用此功能
- 標記需要截圖的位置：`[截圖：{描述}]`
- 包含關鍵設定的說明（例如各選項的用途）

#### 區塊 D：注意事項
- 使用限制
- 容易混淆的地方
- 與相關功能的差異說明

#### 區塊 E：FAQ
- 3-5 個常見問題，從 PRD 的 Open Questions、edge cases、容易誤解的地方推導
- Q&A 格式

### Step 3：確認

將產出的內容呈現給 PM，詢問：
- 哪些區塊需要？哪些不需要？
- 用語是否符合你們 HC 的慣例？
- 有沒有需要補充的情境或 FAQ？
- 這些內容要追加到哪篇現有文章，還是要寫成新文章？
