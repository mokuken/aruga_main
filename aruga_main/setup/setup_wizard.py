# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
ARUGA Setup Wizard — server-side stages.

Provides get_setup_stages() which Frappe calls when the setup wizard
completes. Handles persisting module selections and applying
workspace/role configuration using the new ARUGA Module architecture.
"""

import frappe
from frappe import _

from aruga_main.module_manager import activate_modules


def get_setup_stages(args=None):
	"""
	Return the list of stages Frappe should execute when the setup wizard
	completes. Called via the setup_wizard_stages hook.
	"""
	return [
		{
			"status": _("Configuring ARUGA Modules"),
			"fail_msg": _("Failed to configure ARUGA modules"),
			"tasks": [
				{
					"fn": setup_aruga_modules,
					"args": args,
					"fail_msg": _("Failed to configure ARUGA modules"),
				}
			],
		}
	]


def setup_aruga_modules(args):
	"""
	Main task executed during the setup wizard.

	Reads the selected modules from wizard form data,
	validates they exist as ARUGA Module records,
	and triggers module activation with workspace visibility.
	"""
	if not args:
		return

	# Ensure ARUGA Module records are seeded before activation
	from aruga_main.install import seed_aruga_modules
	seed_aruga_modules()

	# Collect selected module codes from wizard form checkboxes
	selected_modules = []

	all_modules = frappe.get_all(
		"ARUGA Module",
		fields=["name", "module_code"],
	)

	for mod in all_modules:
		# The wizard sends checkbox values using module_code as fieldname
		if args.get(mod.module_code):
			selected_modules.append(mod.name)  # name == module_code (autoname)

	if not selected_modules:
		return

	activate_modules(selected_modules)
