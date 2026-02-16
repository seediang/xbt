---
kind: changed
component: plugin-manager
summary: Process plugins in configured order and show ordered list
---

The plugin manager now supports an explicit `plugin_order` list in `xbt.yml`.

- Plugins listed in `plugin_order` are registered in the given order, which determines
  the invocation order of plugin hooks (important for `xbt_pre_invoke` chaining).
- Discovered but unlisted plugins are appended after the ordered list in discovery order.
- Disabled plugins are always ignored even if present in `plugin_order`.
- The built-in `xbt plugin list` command now prints loaded plugins in the configured
  registration order.

This change ensures deterministic plugin invocation and makes plugin ordering
explicit and auditable via configuration.
