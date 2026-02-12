# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Post-model-sync migration: Recreate module data in new architecture.

This patch runs AFTER Frappe has applied the new DocType JSON changes.
It reads the backed-up data from the pre-model-sync patch and creates:
  - ARUGA Module standalone records
  - ARUGA Module Workspace child table rows
  - ARUGA Enabled Module rows in ARUGA System Configuration

If no backup data exists (fresh install), it seeds from the registry.
"""

import json
import os

import frappe

# Old module_code -> new module_code mapping
# (the old registry used lowercase, new uses uppercase)
CODE_MAPPING = {
	"aruga_accounting": "ARUGA_ACC",
	"aruga_payroll": "ARUGA_PAY",
}


def execute():
	"""Migrate old module data to new architecture or seed fresh."""

	path = os.path.join(frappe.get_site_path(), "aruga_migration_data.json")

	if not os.path.exists(path):
		# Fresh install — seed from registry
		_seed_from_registry()
		return

	with open(path) as f:
		data = json.load(f)

	old_modules = data.get("old_modules", [])
	old_selected = data.get("old_selected", [])

	if old_modules:
		_migrate_modules(old_modules)
		_migrate_selected(old_selected)
	else:
		# No old data — seed fresh
		_seed_from_registry()

	# Clean up migration file
	try:
		os.remove(path)
	except Exception:
		pass

	frappe.db.commit()


def _migrate_modules(old_modules):
	"""Create ARUGA Module records from old child table data."""
	for m in old_modules:
		old_code = m.get("module_code", "")
		new_code = CODE_MAPPING.get(old_code, old_code.upper().replace(" ", "_"))

		if frappe.db.exists("ARUGA Module", new_code):
			continue

		doc = frappe.new_doc("ARUGA Module")
		doc.module_name = m.get("module_title", new_code)
		doc.module_code = new_code
		doc.app_name = m.get("app_name", "")
		doc.description = m.get("description", "")
		doc.icon = m.get("icon", "")
		doc.is_active = m.get("is_active", 0)
		doc.is_core = 0
		doc.order = m.get("display_order", 0)

		# Parse workspaces from newline-separated string
		workspaces_str = m.get("workspaces", "")
		if workspaces_str:
			for idx, ws_name in enumerate(workspaces_str.split("\n")):
				ws_name = ws_name.strip()
				if ws_name:
					doc.append("module_workspaces", {
						"workspace": ws_name,
						"visible": 1,
						"order": idx + 1,
					})

		doc.flags.ignore_validate = True
		doc.insert(ignore_permissions=True)


def _migrate_selected(old_selected):
	"""Update ARUGA System Configuration with migrated enabled modules."""
	if not old_selected:
		return

	config = frappe.get_single("ARUGA System Configuration")
	config.enabled_modules = []

	for s in old_selected:
		old_code = s.get("module_code", "")
		new_code = CODE_MAPPING.get(old_code, old_code.upper().replace(" ", "_"))

		if frappe.db.exists("ARUGA Module", new_code):
			config.append("enabled_modules", {
				"module": new_code,
				"enabled": 1,
			})

	if config.enabled_modules:
		config.last_updated_by = frappe.session.user
		config.last_updated_on = frappe.utils.now()
		config.flags._aruga_applying = True
		config.save(ignore_permissions=True)


def _seed_from_registry():
	"""Seed ARUGA Module records from the central registry."""
	try:
		from aruga_main.install import seed_aruga_modules
		seed_aruga_modules()
	except Exception:
		frappe.log_error("ARUGA Module Seeding Error")
