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
		allowed_ws = _get_allowed_workspace_set()
	except Exception:
		# DocType may not exist yet (pre-migrate). Don't filter.
		return

	if allowed_ws is None:
		# No modules configured yet — show everything
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


def _get_allowed_workspace_set():
	"""
	Build a set of workspace names that should be visible based on
	currently enabled modules in ARUGA System Configuration.

	Returns None if filtering should be skipped (no modules configured).
	"""
	from aruga_main.module_manager import get_enabled_module_names

	enabled = get_enabled_module_names()
	if not enabled:
		return None

	# Get workspaces from enabled modules
	allowed = set()
	workspace_rows = frappe.get_all(
		"ARUGA Module Workspace",
		filters={"parent": ["in", list(enabled)], "visible": 1},
		fields=["workspace"],
	)
	for row in workspace_rows:
		allowed.add(row.workspace)

	return allowed
