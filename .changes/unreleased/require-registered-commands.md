---
kind: changed
component: plugins
summary: Require registered command sets for XbtContext classification
---

Hook contexts now require registered dbt and plugin command sets and use them
exclusively for command classification. This removes fallback logic and makes
the command contract explicit.
