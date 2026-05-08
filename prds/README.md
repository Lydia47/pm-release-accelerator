# PRDs

每份 PRD 是一個專案的需求文件，描述要對 Product Spec 做什麼變更。

## 結構

```
prds/
├── {prd-name}/                   # 進行中的 PRD（kebab-case）
│   ├── evaluation.md             # /product-thinking 評估報告（optional）
│   ├── prd.md                    # PRD 主文（含 Spec Delta）
│   ├── review.md                 # /review-prd 4 角色 subagent 結果
│   ├── test-cases.md             # /gen-test-cases 產出（會被覆蓋）
│   ├── test-runs/                # /test-run 每次執行紀錄（不會被覆蓋）
│   │   └── YYYY-MM-DD.md
│   ├── release-notes.md          # /gen-release-notes（External + Internal）
│   ├── hc-content.md             # /gen-hc-content（Help Center 素材）
│   └── verification-{date}.md    # /verify 上線前驗證報告
│
└── archive/                      # 已歸檔
    └── YYYY-MM-DD-{prd-name}/
```

## 生命週期

```
draft → in-review → approved → archived
```

PRD frontmatter 的 `status` 欄位追蹤狀態。歸檔由 `/archive-prd` 處理 — 會把 Spec Delta 更新到對應的 `specs/{domain}/spec.md`。

## 如何開始

```bash
# 1. 跟 AI 對話探索問題與解法
#    需要時用 /product-thinking 做結構化評估
#    方向確定後 AI 會引導下一步

# 2. 建立 PRD
/new-prd
```
