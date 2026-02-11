# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

import frappe

from aruga_main.modules_registry import ARUGA_MODULES


def after_install():
	"""Called after aruga_main is installed. Seeds available module data."""
	seed_available_modules()


@frappe.whitelist()
def seed_available_modules():
	"""
	Populate the Available ARUGA Modules singleton with module definitions
	based on which ARUGA apps are currently installed in the container.

	This is safe to call multiple times — it replaces the child table each time.
	"""
	installed_apps = frappe.get_installed_apps()

	doc = frappe.get_single("Available ARUGA Modules")
	doc.available_modules = []

	for module_def in ARUGA_MODULES:
		if module_def["app_name"] in installed_apps:
			doc.append(
				"available_modules",
				{
					"module_code": module_def["module_code"],
					"module_title": module_def["module_title"],
					"app_name": module_def["app_name"],
					"description": module_def["description"],
					"icon": module_def.get("icon", ""),
					"is_active": 0,
					"display_order": module_def["display_order"],
					"workspaces": "\n".join(module_def["workspaces"]),
					"roles": "\n".join(module_def["roles"]),
				},
			)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
