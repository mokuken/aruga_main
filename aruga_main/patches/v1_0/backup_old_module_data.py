# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Pre-model-sync migration: Back up old module data before schema changes.

This patch runs BEFORE Frappe applies the new DocType JSON changes.
It reads the old child-table-based data from:
  - tabARUGA Module (child table rows from ARUGA Available Modules)
  - tabARUGA Selected Module (child table rows from ARUGA System Configuration)

And saves it to a temporary JSON file in the site directory for the
post-model-sync patch to consume.
"""

import json
import os

import frappe


def execute():
	"""Back up existing module data before the schema migration."""

	migration_data = {
		"old_modules": [],
		"old_selected": [],
	}

	# Check if the old ARUGA Module table exists and has child-table-style data
	try:
		if frappe.db.table_exists("tabARUGA Module"):
			# Check if it still has 'parent' column (child table structure)
			columns = frappe.db.get_table_columns("ARUGA Module")
			if "parent" in columns:
				old_modules = frappe.db.sql(
					"""
					SELECT module_code, module_title, app_name, description,
						   icon, is_active, display_order, workspaces, roles
					FROM `tabARUGA Module`
					WHERE parent IS NOT NULL AND parent != ''
					""",
					as_dict=True,
				)
				migration_data["old_modules"] = [dict(m) for m in old_modules]

				# Clean up old child table rows to prevent conflicts during schema change
				frappe.db.sql(
					"DELETE FROM `tabARUGA Module` WHERE parent IS NOT NULL AND parent != ''"
				)
	except Exception:
		pass

	# Back up old selected modules
	try:
		if frappe.db.table_exists("tabARUGA Selected Module"):
			old_selected = frappe.db.sql(
				"""
				SELECT module_code, module_title
				FROM `tabARUGA Selected Module`
				WHERE parent = 'ARUGA System Configuration'
				""",
				as_dict=True,
			)
			migration_data["old_selected"] = [dict(s) for s in old_selected]
	except Exception:
		pass

	# Also back up system_initialized flag if it exists
	try:
		columns = frappe.db.get_table_columns("ARUGA System Configuration")
		if "system_initialized" in columns:
			val = frappe.db.sql(
				"SELECT system_initialized FROM `tabARUGA System Configuration` LIMIT 1"
			)
			migration_data["system_initialized"] = bool(val and val[0][0])
	except Exception:
		migration_data["system_initialized"] = False

	# Save migration data to site directory
	path = os.path.join(frappe.get_site_path(), "aruga_migration_data.json")
	with open(path, "w") as f:
		json.dump(migration_data, f, indent=2, default=str)

	frappe.db.commit()
