---
name: triple-a-review
description: "**Use when user wants a lightweight requirement-completeness check** — single requirement (not full PRD), phrases like triple-a / AAA review / 審查需求 / 需求檢查 / 這個需求完整嗎 / requirement review. Applies Align/Author/Audit framework from PM/PD/Eng angles. For full PRD review with 4-role parallel feedback (PM/Eng/QA/PD), use review-prd instead."
user_invocable: true
---

# Triple-A Review — 跨職能需求審查

## 任務
使用 Triple-A 框架（Align / Author / Audit）從 PM、PD、Eng 三個角度審查功能需求或 Brief，找出潛在問題與缺漏。

## 輸入
使用者提供以下任一項：
- Google Docs Brief 連結（透過 gws CLI 讀取）
- 本地 markdown 檔案路徑
- 直接貼上需求文字

## 步驟

### Phase 1: Align（對齊）— PM 視角
- 這個需求要解決什麼問題？目標使用者是誰？
- 與現有功能是否衝突或重疊？（讀取 codebase 比對）
- 成功指標（KPI / metrics）是否明確？
- 有沒有遺漏的 edge case 或例外情境？
- 各語系 / 各市場是否有差異需求？

### Phase 2: Author（產出）— PD/Eng 視角
- 設計稿 / wireframe 是否完整？
- 現有 component 能否複用？需要新建哪些？
- API 需要哪些變更？是否需要新的 endpoint？
- 資料模型是否需要調整？（讀取 DB schema 或 types）
- 預估工作量與影響範圍

### Phase 3: Audit（審核）— 品質視角
- 安全性風險（XSS、SQL injection、權限控管）
- 效能影響（N+1 query、大量 render、API 回應時間）
- 向下相容性（舊版 API、舊版 APP）
- 測試案例是否覆蓋核心流程？
- 國際化（i18n）是否考慮到？

## 輸出格式

```
## Triple-A Review Report

### ✅ Align（對齊）
- [findings...]
- 風險等級：🟢 低 / 🟡 中 / 🔴 高

### ✅ Author（產出）
- [findings...]
- 預估影響檔案：[list]
- 預估工時：[range]

### ✅ Audit（審核）
- [findings...]
- 安全性：🟢/🟡/🔴
- 效能：🟢/🟡/🔴

### 📋 Action Items
1. [prioritized list of things to address before development]
```
