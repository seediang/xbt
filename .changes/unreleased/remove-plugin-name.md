---
kind: changed
component: plugins
summary: Remove plugin_name from XbtContext
---

Hook contexts no longer include a plugin_name field since plugins already know
their identity.
