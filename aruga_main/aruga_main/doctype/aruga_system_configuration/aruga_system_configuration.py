# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ARUGASystemConfiguration(Document):
	def validate(self):
		if not self.selected_modules:
			frappe.throw(_("Please select at least one module."))

	def on_update(self):
		"""
		When the admin manually updates module selection from the form,
		re-apply workspace visibility based on the new selection.
		"""
		# Guard: if activate_modules() triggered this save, do nothing.
		if self.flags.get("_aruga_activating"):
			return

		selected_codes = [row.module_code for row in self.selected_modules]
		if selected_codes:
			from aruga_main.module_manager import (
				_apply_workspace_visibility,
				_get_db_module_rows,
				_update_available_module_flags,
			)
			from aruga_main.modules_registry import ARUGA_MODULES

			# Prefer database rows; fall back to hardcoded registry
			db_rows = _get_db_module_rows()
			if db_rows:
				registry_map = {
					row.module_code: {
						"module_code": row.module_code,
						"module_title": row.module_title,
						"workspaces": [ws.strip() for ws in (row.workspaces or "").split("\n") if ws.strip()],
						"roles": [r.strip() for r in (row.roles or "").split("\n") if r.strip()],
					}
					for row in db_rows
				}
			else:
				registry_map = {m["module_code"]: m for m in ARUGA_MODULES}

			_update_available_module_flags(selected_codes)
			_apply_workspace_visibility(selected_codes, registry_map)
			frappe.db.commit()
			frappe.clear_cache()
			frappe.msgprint(_("Module configuration applied successfully."), alert=True)
