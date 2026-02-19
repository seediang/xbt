---
kind: changed
component: plugin-manager
summary: Rename built-in plugins directory to builtin_plugins
---

Built-in plugins are now discovered from src/xbt/builtin_plugins instead of
src/xbt/_plugins. References and tests were updated accordingly.
