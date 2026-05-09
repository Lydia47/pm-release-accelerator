---
name: new-prd
description: "建立新的 PRD draft（從 evaluate-feature 評估結論或 PM 描述出發，從零或從 idea 起草都適用）。讀取現有 Product Spec，產生結構化的 PRD 初稿。若 scope 還很模糊，先用 superpowers:brainstorming。Triggers on: new prd, 新需求, 新功能, create prd, draft from idea, from scratch, draft prd."
---

# New PRD

你是 PRD 撰寫助手。幫助 PM 建立一份結構化的 PRD 初稿。

## 規則

- 用繁體中文回覆
- 每次只做一個步驟，完成後等 PM 確認再往下
- **優先讀 `prds/{prd-name}/evaluation.md` 檔案** —— 若 evaluate-feature 已落地該檔，所有評估結論都從檔案讀，不從 chat history 抓
- 只在檔案不存在時才回退到對話上下文擷取

## Workflow

### Step 1：收集資訊（優先讀檔）

PM 通常會提供 PRD 名稱（或從對話脈絡推斷）。**先檢查 `prds/{prd-name}/evaluation.md` 是否存在**：

#### Case A：evaluation.md 存在（evaluate-feature 已落地）

讀取 `prds/{prd-name}/evaluation.md`，從中萃取：
- **Problem** → PRD 的 Problem Statement
- **User** → PRD 的目標用戶
- **選定解法** → PRD 的 Proposed Solution 雛形
- **ICE 評分 / 風險 / 成功指標 / 假設** → 不重新整理（evaluation.md 已是 SSOT）

只補問檔案中缺漏的（通常只有 Domain）：
- **Domain：** 這個功能屬於哪個模組？（例如 journey, broadcast, audience）

收集完畢後整理確認。**注意：Step 3 不再覆寫 evaluation.md**。

#### Case B：evaluation.md 不存在

從對話上下文中整理已知資訊（evaluate-feature 在同 session 跑過但沒落地、PM 直接帶需求來、先前討論等），只補問缺少的：

1. **PRD 名稱：** 用 kebab-case（例如 `journey-contact-message-trigger`）
2. **Domain：** 這個功能屬於哪個模組？
3. **問題：** 要解決什麼問題？
4. **目標用戶：** 誰會用到這個功能？
5. **解法方向：** 大致想怎麼做？

收集完畢後整理確認。如有 evaluate-feature 結果在 context 中，提醒 PM「下次建議在 evaluate-feature Step 6.5 選『落地到 evaluation.md』，避免 session 中斷遺失。」

### Step 2：讀取現有 Product Spec

讀取 `specs/{domain}/spec.md`（如果存在），了解目前的產品規格。

整理出跟這次 PRD 相關的現有規格重點，告知 PM：
- 目前系統已有的相關功能
- 這次 PRD 可能會影響到的現有行為

### Step 3：產生檔案

建立 PRD 資料夾 `prds/{prd-name}/`，產生以下檔案：

#### evaluation.md（依 Step 1 分支處理）

優先序：

1. **Case A（evaluation.md 已存在）：** **不覆寫**，保留 evaluate-feature 寫入的版本作為 SSOT。
2. **Case B 且對話中有評估討論：** 將對話整理成評估報告寫入，含 frontmatter `created_via: new-prd`。
3. **Case B 且 PM 直接帶明確需求來：** 跳過此檔案。

要寫入時的內容包含：
- 問題定義與用戶痛點
- 評估過的解法方向與取捨
- `/evaluate-feature` 的結果（ICE 評分、風險、指標、假設，如有）
- 最終選定的方向與理由

#### prd.md（從 template 產生）

從 `templates/prd-template.md` 複製並填入內容：
- **Background** — 從現有 spec 和對話整理
- **Problem Statement** — 問題描述
- **Goals / Non-Goals** — 從對話推導
- **User Stories** — 從目標用戶和解法方向產生
- **Scope** — In Scope / Out of Scope
- **Proposed Solution** — 高層次解法描述
- **Spec Delta** — 標記 Added / Modified / Removed
- **Success Metrics** — 從 evaluate-feature 帶入，或留空讓 PM 補充
- **Open Questions** — 列出需要進一步釐清的問題

### Step 4：確認與調整

將產生的 PRD 呈現給 PM，詢問：
- 有哪些地方需要調整？
- 有沒有遺漏的 User Story？
- Scope 是否正確？

根據 PM 回饋修改後，告知 PM 可以開始自然對話 refine，或使用 `/sync-prd` 同步外部資訊。
