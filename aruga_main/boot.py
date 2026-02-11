# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Boot-time workspace filtering based on ARUGA module configuration.

Hooks into Frappe's extend_bootinfo mechanism to remove workspaces
from the Desk sidebar that do not belong to any active ARUGA module.
"""

import frappe

from aruga_main.modules_registry import SYSTEM_WORKSPACES


def extend_bootinfo(bootinfo):
	"""
	Filter bootinfo.allowed_workspaces so the Desk sidebar only shows
	workspaces belonging to active ARUGA modules plus system workspaces.

	Called on every page load via the extend_bootinfo hook.
	"""
	try:
		config = frappe.get_single("ARUGA System Configuration")
	except Exception:
		# DocType may not exist yet (pre-migrate). Don't filter.
		return

	if not config.system_initialized:
		# Setup hasn't run yet — show everything so the admin can proceed.
		return

	allowed_ws = _get_allowed_workspace_set(config)
	if allowed_ws is None:
		return

	if hasattr(bootinfo, "allowed_workspaces") and bootinfo.allowed_workspaces:
		bootinfo.allowed_workspaces = [
			ws
			for ws in bootinfo.allowed_workspaces
			if _workspace_is_allowed(ws, allowed_ws)
		]


def _workspace_is_allowed(ws, allowed_ws):
	"""Check if a workspace should remain visible."""
	name = ws.get("name", "")
	title = ws.get("title", "")

	# Always keep system workspaces
	if name in SYSTEM_WORKSPACES or title in SYSTEM_WORKSPACES:
		return True

	# Keep private (user-specific) workspaces
	if ws.get("for_user"):
		return True

	# Check against active module workspace list
	return name in allowed_ws or title in allowed_ws


def _get_allowed_workspace_set(config):
	"""
	Build a set of workspace names that should be visible based on
	currently active modules in ARUGA System Configuration.

	Returns None if filtering should be skipped.
	"""
	selected_codes = {row.module_code for row in config.selected_modules}
	if not selected_codes:
		return None

	try:
		available = frappe.get_single("Available ARUGA Modules")
	except Exception:
		return None

	allowed = set()
	for module in available.available_modules:
		if module.module_code in selected_codes:
			workspaces_str = (module.workspaces or "").strip()
			if workspaces_str:
				allowed.update(ws.strip() for ws in workspaces_str.split("\n") if ws.strip())

	return allowed
