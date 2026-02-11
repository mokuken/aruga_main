# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Module Manager — core activation / deactivation logic.

This module is called from:
1. The setup wizard (first-time configuration)
2. The ARUGA System Configuration doctype form (manual updates)
3. Whitelisted API for programmatic activation
"""

import frappe
from frappe import _

from aruga_main.modules_registry import ARUGA_MODULES, SYSTEM_WORKSPACES


def activate_modules(module_codes, user=None):
	"""
	Activate the given ARUGA module codes and deactivate the rest.

	Args:
	    module_codes: list of module_code strings, e.g. ["aruga_accounting", "aruga_payroll"]
	    user: the user performing the change (defaults to current session user)
	"""
	if not module_codes:
		frappe.throw(_("Please select at least one module to activate."))

	user = user or frappe.session.user

	# Build the lookup for the module registry
	registry_map = {m["module_code"]: m for m in ARUGA_MODULES}

	# Update ARUGA System Configuration
	config = frappe.get_single("ARUGA System Configuration")
	config.selected_modules = []

	for code in module_codes:
		if code not in registry_map:
			continue
		module_def = registry_map[code]
		config.append(
			"selected_modules",
			{
				"module_code": module_def["module_code"],
				"module_title": module_def["module_title"],
			},
		)

	config.system_initialized = 1
	config.configuration_date = frappe.utils.now()
	config.configured_by = user
	# Prevent on_update from calling activate_modules again (infinite recursion)
	config.flags._aruga_activating = True
	config.save(ignore_permissions=True)

	# Update Available ARUGA Modules — mark active flags
	_update_available_module_flags(module_codes)

	# Apply workspace visibility
	_apply_workspace_visibility(module_codes, registry_map)

	frappe.db.commit()


def deactivate_all_modules():
	"""Reset system to no active modules (rarely used)."""
	config = frappe.get_single("ARUGA System Configuration")
	config.selected_modules = []
	config.system_initialized = 0
	config.configuration_date = frappe.utils.now()
	config.configured_by = frappe.session.user
	config.save(ignore_permissions=True)

	_update_available_module_flags([])
	_unhide_all_workspaces()
	frappe.db.commit()


def _update_available_module_flags(active_codes):
	"""Update is_active flags on Available ARUGA Modules child table."""
	try:
		doc = frappe.get_single("Available ARUGA Modules")
		for row in doc.available_modules:
			row.is_active = 1 if row.module_code in active_codes else 0
		doc.save(ignore_permissions=True)
	except Exception:
		pass


def _apply_workspace_visibility(active_codes, registry_map):
	"""
	Show/hide workspaces on the Desk based on active modules.

	Strategy:
	  - Identify all valid workspaces for the selected active modules
	  - Fetch ALL public/system workspaces from the database
	  - Hide (public=0) anything not in the active set (except system workspaces)
	  - Show (public=1) everything in the active set
	"""
	active_workspaces = set()

	# Collect allowed workspaces from active modules
	for module_def in ARUGA_MODULES:
		if module_def["module_code"] in active_codes:
			active_workspaces.update(module_def["workspaces"])

	# Treat system workspaces as always active
	active_workspaces.update(SYSTEM_WORKSPACES)

	# Fetch all existing workspaces (name, public, is_hidden, for_user)
	all_workspaces = frappe.get_all(
		"Workspace",
		fields=["name", "public", "is_hidden", "for_user"]
	)

	for ws in all_workspaces:
		# Skip private user workspaces entirely
		if ws.for_user:
			continue

		ws_name = ws.name

		if ws_name in active_workspaces:
			# Ensure it's visible if it's currently hidden
			if not ws.public or ws.is_hidden:
				_set_workspace_hidden(ws_name, hidden=False)
		else:
			# Hide it if it's currently public
			if ws.public:
				_set_workspace_hidden(ws_name, hidden=True)


def _set_workspace_hidden(workspace_name, hidden=True):
	"""
	Set the `public` flag on a Workspace document to control visibility in sidebar.
	
	- hidden=True  -> public=0 (hidden from sidebar)
	- hidden=False -> public=1 (shown in sidebar)
	"""
	try:
		if frappe.db.exists("Workspace", workspace_name):
			frappe.db.set_value(
				"Workspace",
				workspace_name,
				"public",
				0 if hidden else 1,
				update_modified=False,
			)
			# We also ensure is_hidden is 0 so it's not double-hidden if it becomes public
			if not hidden:
				frappe.db.set_value(
					"Workspace",
					workspace_name,
					"is_hidden",
					0,
					update_modified=False,
				)
	except Exception:
		# Workspace may not exist if the app isn't installed yet — safe to skip
		pass


def _unhide_all_workspaces():
	"""Unhide all known module workspaces (used during deactivation)."""
	for module_def in ARUGA_MODULES:
		for ws_name in module_def["workspaces"]:
			_set_workspace_hidden(ws_name, hidden=False)


# --- Whitelisted API ---

@frappe.whitelist()
def activate_modules_api(module_codes):
	"""
	API endpoint to activate ARUGA modules.

	Args:
	    module_codes: JSON list of module_code strings
	"""
	import json

	if isinstance(module_codes, str):
		module_codes = json.loads(module_codes)

	if not isinstance(module_codes, list):
		frappe.throw(_("module_codes must be a list"))

	# Only System Manager can change module configuration
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Manager can activate modules"), frappe.PermissionError)

	activate_modules(module_codes)


@frappe.whitelist()
def get_active_modules():
	"""Return list of currently active module codes."""
	try:
		config = frappe.get_single("ARUGA System Configuration")
		return [row.module_code for row in config.selected_modules]
	except Exception:
		return []


@frappe.whitelist()
def get_available_modules():
	"""Return list of available ARUGA modules with their metadata."""
	installed_apps = frappe.get_installed_apps()
	result = []
	for module_def in ARUGA_MODULES:
		if module_def["app_name"] in installed_apps:
			result.append(
				{
					"module_code": module_def["module_code"],
					"module_title": module_def["module_title"],
					"description": module_def["description"],
					"icon": module_def.get("icon", ""),
					"display_order": module_def["display_order"],
				}
			)
	return result


@frappe.whitelist()
def get_all_modules():
	"""Return list of ALL ARUGA modules with installed status."""
	installed_apps = frappe.get_installed_apps()
	result = []
	for module_def in ARUGA_MODULES:
		result.append(
			{
				"module_code": module_def["module_code"],
				"module_title": module_def["module_title"],
				"description": module_def["description"],
				"icon": module_def.get("icon", ""),
				"display_order": module_def["display_order"],
				"installed": module_def["app_name"] in installed_apps
			}
		)
	return result
