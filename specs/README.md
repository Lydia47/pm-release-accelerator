# Product Specs

Product Spec 是各 domain 的 SSOT，描述系統**目前**的行為。

## 結構

```
specs/{domain}/
├── spec.md                       # 主 spec（含 Overview, Glossary, Actors, Data Model, Lifecycle, Capabilities index）
└── capabilities/
    └── {capability-name}.md      # 拆分的 capability spec（REQ + Scenarios）
```

當一個 capability 有 3+ REQs 或 5+ scenarios 時拆出獨立檔案，否則放主 spec。

## 如何建立

- **既有 codebase** → `/gen-product-spec` 平行 subagent 讀 source code 反向產出
- **新功能** → PRD 歸檔時 `/archive-prd` 自動把 Spec Delta 更新進對應 spec

## 參考

模板：[`templates/spec-template.md`](../templates/spec-template.md)

範例：可參考 [pm-hub 的 specs/](https://github.com/chatbotgang/pm-hub/tree/main/specs)（journey, prize 兩個 domain 的完整實例）
