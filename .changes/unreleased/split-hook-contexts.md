---
kind: changed
component: plugins
summary: Split hook contexts by lifecycle stage
---

Hooks now receive InitContext, PreInvokeContext, or PostInvokeContext instead of
a single shared context. Each context only includes fields populated for that
hook (for example, only PostInvokeContext includes `result`).
