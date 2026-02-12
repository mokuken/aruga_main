# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Installation and seeding logic for aruga_main.

Seeds ARUGA Module records from the modules_registry on first install
and provides a whitelisted API to refresh/reseed at any time.
"""

import frappe

from aruga_main.modules_registry import ARUGA_MODULES


def after_install():
	"""Called after aruga_main is installed. Seeds ARUGA Module records."""
	seed_aruga_modules()


@frappe.whitelist()
def seed_aruga_modules():
	"""
	Create or update ARUGA Module records from the central registry,
	filtered to only include modules whose app is installed.

	Safe to call multiple times — uses insert-or-update logic.
	"""
	installed_apps = frappe.get_installed_apps()

	for module_def in ARUGA_MODULES:
		# Only seed modules whose app is installed
		if module_def["app_name"] not in installed_apps:
			continue

		module_code = module_def["module_code"]

		if frappe.db.exists("ARUGA Module", module_code):
			# Update existing record (don't overwrite user edits to is_active)
			doc = frappe.get_doc("ARUGA Module", module_code)
			doc.module_name = module_def["module_name"]
			doc.app_name = module_def["app_name"]
			doc.description = module_def["description"]
			doc.icon = module_def.get("icon", "")
			doc.is_core = module_def.get("is_core", 0)
			doc.order = module_def.get("order", 0)

			# Sync workspaces: add missing ones, keep existing
			existing_ws = {row.workspace for row in doc.module_workspaces}
			for ws_name in module_def.get("workspaces", []):
				if ws_name not in existing_ws:
					doc.append("module_workspaces", {
						"workspace": ws_name,
						"visible": 1,
						"order": 0,
					})

			doc.save(ignore_permissions=True)
		else:
			# Create new record
			doc = frappe.new_doc("ARUGA Module")
			doc.module_name = module_def["module_name"]
			doc.module_code = module_code
			doc.app_name = module_def["app_name"]
			doc.description = module_def["description"]
			doc.icon = module_def.get("icon", "")
			doc.is_active = 0
			doc.is_core = module_def.get("is_core", 0)
			doc.order = module_def.get("order", 0)

			for ws_name in module_def.get("workspaces", []):
				doc.append("module_workspaces", {
					"workspace": ws_name,
					"visible": 1,
					"order": 0,
				})

			doc.insert(ignore_permissions=True)

	frappe.db.commit()
