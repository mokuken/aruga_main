# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Module Manager — core activation / deactivation / visibility logic.

This module is called from:
1. The setup wizard (first-time configuration)
2. The ARUGA System Configuration doctype on_update (manual changes)
3. The after_migrate hook (ensure consistency after bench migrate)
4. Whitelisted API for programmatic activation
"""

import frappe
from frappe import _

from aruga_main.modules_registry import SYSTEM_WORKSPACES


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def activate_modules(module_codes, user=None):
	"""
	Activate the given ARUGA module codes and deactivate the rest.

	This is the main entry point called from setup wizard and API.
	It updates both the ARUGA Module records (is_active) and
	the ARUGA System Configuration singleton.

	Args:
		module_codes: list of module_code strings, e.g. ["ARUGA_ACC", "ARUGA_PAY"]
		user: the user performing the change (defaults to current session user)
	"""
	if not module_codes:
		frappe.throw(_("Please select at least one module to activate."))

	user = user or frappe.session.user
	module_codes = set(module_codes)

	# Validate all codes exist
	for code in module_codes:
		if not frappe.db.exists("ARUGA Module", code):
			frappe.throw(_("Module '{0}' does not exist.").format(code))

	# Update is_active flags on ARUGA Module records
	all_modules = frappe.get_all("ARUGA Module", fields=["name", "is_core"])
	for mod in all_modules:
		new_active = 1 if mod.name in module_codes else 0
		frappe.db.set_value(
			"ARUGA Module", mod.name, "is_active", new_active, update_modified=False
		)

	# Update ARUGA System Configuration
	config = frappe.get_single("ARUGA System Configuration")
	config.enabled_modules = []

	for code in module_codes:
		config.append("enabled_modules", {"module": code, "enabled": 1})

	config.last_updated_by = user
	config.last_updated_on = frappe.utils.now()
	# Prevent on_update from re-applying (infinite recursion guard)
	config.flags._aruga_applying = True
	config.save(ignore_permissions=True)

	# Apply workspace visibility
	apply_workspace_visibility(module_codes)

	frappe.db.commit()


def deactivate_all_modules():
	"""Reset system to no active modules (rarely used)."""
	# Set all modules inactive
	frappe.db.sql(
		"UPDATE `tabARUGA Module` SET is_active = 0 WHERE is_core = 0"
	)

	config = frappe.get_single("ARUGA System Configuration")
	config.enabled_modules = []
	config.last_updated_by = frappe.session.user
	config.last_updated_on = frappe.utils.now()
	config.flags._aruga_applying = True
	config.save(ignore_permissions=True)

	_unhide_all_workspaces()
	frappe.db.commit()


# ---------------------------------------------------------------------------
# Workspace Visibility
# ---------------------------------------------------------------------------

def apply_workspace_visibility(enabled_module_names=None):
	"""
	Show/hide workspaces on the Desk based on active modules.

	Strategy:
	  - Collect all workspaces mapped to enabled modules
	  - Always keep SYSTEM_WORKSPACES visible
	  - Hide workspaces belonging to disabled modules
	  - Never touch private (for_user) workspaces

	Uses `is_hidden` flag — does NOT delete or modify `public` flag.

	Args:
		enabled_module_names: set/list of ARUGA Module names that are enabled.
			If None, reads from ARUGA System Configuration.
	"""
	if enabled_module_names is None:
		enabled_module_names = get_enabled_module_names()

	enabled_module_names = set(enabled_module_names)

	# Collect workspaces that should be visible
	active_workspaces = set()
	module_workspace_rows = frappe.get_all(
		"ARUGA Module Workspace",
		filters={"parent": ["in", list(enabled_module_names)], "visible": 1},
		fields=["workspace"],
	)
	for row in module_workspace_rows:
		active_workspaces.add(row.workspace)

	# Always keep system workspaces visible
	active_workspaces.update(SYSTEM_WORKSPACES)

	# Collect ALL workspaces controlled by ANY ARUGA module (active or not)
	all_controlled_workspaces = set()
	all_module_ws_rows = frappe.get_all(
		"ARUGA Module Workspace",
		fields=["workspace"],
	)
	for row in all_module_ws_rows:
		all_controlled_workspaces.add(row.workspace)

	# Apply visibility changes
	all_workspaces = frappe.get_all(
		"Workspace",
		fields=["name", "public", "is_hidden", "for_user"],
	)

	for ws in all_workspaces:
		# Skip private user workspaces entirely
		if ws.for_user:
			continue

		ws_name = ws.name

		if ws_name in active_workspaces:
			# Should be visible
			if ws.is_hidden:
				frappe.db.set_value(
					"Workspace", ws_name, "is_hidden", 0, update_modified=False
				)
		elif ws_name in all_controlled_workspaces:
			# Belongs to a disabled module — hide it
			if not ws.is_hidden:
				frappe.db.set_value(
					"Workspace", ws_name, "is_hidden", 1, update_modified=False
				)
		# Workspaces not controlled by any module are left untouched


def apply_workspace_visibility_on_migrate():
	"""
	Hook called after bench migrate to ensure workspace visibility
	is consistent with the current ARUGA module configuration.
	"""
	try:
		apply_workspace_visibility()
	except Exception:
		# Safe to skip if tables don't exist yet
		pass


def _unhide_all_workspaces():
	"""Unhide all workspaces controlled by ARUGA modules (used during deactivation)."""
	all_module_ws = frappe.get_all(
		"ARUGA Module Workspace",
		fields=["workspace"],
	)
	for row in all_module_ws:
		if frappe.db.exists("Workspace", row.workspace):
			frappe.db.set_value(
				"Workspace", row.workspace, "is_hidden", 0, update_modified=False
			)


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

def get_enabled_module_names():
	"""Return set of enabled ARUGA Module names from System Configuration."""
	try:
		config = frappe.get_single("ARUGA System Configuration")
		return {
			row.module
			for row in (config.enabled_modules or [])
			if row.enabled and row.module
		}
	except Exception:
		return set()


def get_all_aruga_modules():
	"""Return all ARUGA Module records as list of dicts."""
	return frappe.get_all(
		"ARUGA Module",
		fields=["name", "module_name", "module_code", "description", "icon",
				"is_active", "is_core", "order", "app_name"],
		order_by="order asc",
	)


# ---------------------------------------------------------------------------
# Whitelisted API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def activate_modules_api(module_codes):
	"""
	API endpoint to activate ARUGA modules.

	Args:
		module_codes: JSON list of module_code strings
	"""
	import json as _json

	if isinstance(module_codes, str):
		module_codes = _json.loads(module_codes)

	if not isinstance(module_codes, list):
		frappe.throw(_("module_codes must be a list"))

	# Only System Manager can change module configuration
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Manager can activate modules"), frappe.PermissionError)

	activate_modules(module_codes)


@frappe.whitelist()
def get_active_modules():
	"""Return list of currently active module codes (names)."""
	return list(get_enabled_module_names())


@frappe.whitelist()
def get_available_modules():
	"""
	Return list of available ARUGA modules for selection UIs.

	Only includes modules whose app is currently installed.
	"""
	installed_apps = frappe.get_installed_apps()

	modules = frappe.get_all(
		"ARUGA Module",
		fields=["name", "module_name", "module_code", "description", "icon",
				"order", "app_name", "is_active"],
		order_by="order asc",
	)

	result = []
	for mod in modules:
		# Only include if app is installed (or app_name is not set)
		if mod.app_name and mod.app_name not in installed_apps:
			continue
		result.append({
			"module_code": mod.module_code,
			"module_name": mod.module_name,
			"description": mod.description or "",
			"icon": mod.icon or "",
			"order": mod.order or 0,
			"is_active": mod.is_active,
		})

	return result


@frappe.whitelist()
def get_all_modules():
	"""
	Return list of ALL ARUGA modules with installed status.

	Used by the setup wizard to show all modules regardless of installation.
	"""
	installed_apps = frappe.get_installed_apps()

	modules = frappe.get_all(
		"ARUGA Module",
		fields=["name", "module_name", "module_code", "description", "icon",
				"order", "app_name", "is_active"],
		order_by="order asc",
	)

	result = []
	for mod in modules:
		result.append({
			"module_code": mod.module_code,
			"module_name": mod.module_name,
			"description": mod.description or "",
			"icon": mod.icon or "",
			"order": mod.order or 0,
			"installed": (mod.app_name in installed_apps) if mod.app_name else True,
			"is_active": mod.is_active,
		})

	return result
