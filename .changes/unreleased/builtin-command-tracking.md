---
kind: changed
component: plugins
summary: Add builtin command tracking to XbtContext
---

Hook contexts now expose registered builtin command sets and an
`is_builtin_command` property for commands originating from xbt-core
built-in plugins.
