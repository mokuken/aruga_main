# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class ARUGASystemConfiguration(Document):
	def validate(self):
		self._validate_enabled_modules()

	def _validate_enabled_modules(self):
		"""Ensure at least one module is enabled and prevent disabling core modules."""
		enabled_count = 0
		for row in self.enabled_modules or []:
			if row.enabled:
				enabled_count += 1

			# Check if trying to disable a core module
			if not row.enabled and row.module:
				is_core = frappe.db.get_value("ARUGA Module", row.module, "is_core")
				if is_core:
					frappe.throw(
						_("Core module '{0}' cannot be disabled.").format(row.module)
					)

		if not enabled_count and self.enabled_modules:
			frappe.throw(_("Please enable at least one module."))

	def on_update(self):
		"""
		When the configuration is saved, apply module activation/deactivation
		and workspace visibility changes.
		"""
		# Guard: if apply_configuration() triggered this save, do nothing
		if self.flags.get("_aruga_applying"):
			return

		self._log_configuration_change()
		self._apply_module_states()
		self._apply_workspace_visibility()

		self.db_set("last_updated_by", frappe.session.user, update_modified=False)
		self.db_set("last_updated_on", frappe.utils.now(), update_modified=False)

		frappe.db.commit()
		frappe.clear_cache()
		frappe.msgprint(_("Module configuration applied successfully."), alert=True)

	def _get_enabled_module_names(self):
		"""Return set of module names (ARUGA Module doctype names) that are enabled."""
		return {
			row.module for row in (self.enabled_modules or []) if row.enabled and row.module
		}

	def _apply_module_states(self):
		"""Set is_active on each ARUGA Module based on enabled_modules selection."""
		enabled = self._get_enabled_module_names()

		all_modules = frappe.get_all("ARUGA Module", fields=["name"])
		for mod in all_modules:
			new_state = 1 if mod.name in enabled else 0
			frappe.db.set_value(
				"ARUGA Module", mod.name, "is_active", new_state, update_modified=False
			)

	def _apply_workspace_visibility(self):
		"""Show/hide workspaces based on enabled modules and their workspace mappings."""
		from aruga_main.module_manager import apply_workspace_visibility

		enabled = self._get_enabled_module_names()
		apply_workspace_visibility(enabled)

	def _log_configuration_change(self):
		"""Create an ARUGA Configuration Log entry for audit trail."""
		try:
			# Get previous state
			old_config = frappe.get_all(
				"ARUGA Enabled Module",
				filters={"parent": "ARUGA System Configuration", "parentfield": "enabled_modules"},
				fields=["module", "enabled"],
			)
			previous = [{"module": r.module, "enabled": r.enabled} for r in old_config]

			# New state from current form
			new = [
				{"module": row.module, "enabled": row.enabled}
				for row in (self.enabled_modules or [])
			]

			# Only log if there's an actual change
			if json.dumps(previous, sort_keys=True) != json.dumps(new, sort_keys=True):
				frappe.get_doc(
					{
						"doctype": "ARUGA Configuration Log",
						"changed_by": frappe.session.user,
						"date": frappe.utils.now(),
						"previous_config": json.dumps(previous, indent=2),
						"new_config": json.dumps(new, indent=2),
					}
				).insert(ignore_permissions=True)
		except Exception:
			# Don't block save if logging fails
			frappe.log_error("ARUGA Configuration Log Error")
