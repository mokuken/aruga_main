# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ARUGAModule(Document):
	def validate(self):
		self._validate_module_code()
		self._validate_workspaces()

	def _validate_module_code(self):
		"""Ensure module_code is uppercase with underscores only."""
		if self.module_code:
			sanitized = self.module_code.strip().upper().replace(" ", "_")
			self.module_code = sanitized

	def _validate_workspaces(self):
		"""Ensure linked workspaces exist."""
		for row in self.module_workspaces or []:
			if row.workspace and not frappe.db.exists("Workspace", row.workspace):
				frappe.msgprint(
					_("Workspace '{0}' does not exist and will be skipped during visibility updates.").format(
						row.workspace
					),
					indicator="orange",
					alert=True,
				)

	def on_trash(self):
		"""Prevent deletion of core modules."""
		if self.is_core:
			frappe.throw(_("Core module '{0}' cannot be deleted.").format(self.module_name))
