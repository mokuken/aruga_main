# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
ARUGA Setup Wizard — server-side stages.

Provides get_setup_stages() which Frappe calls when the setup wizard
completes. Handles persisting module selections and applying
workspace/role configuration.
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
	persists them into ARUGA System Configuration,
	and triggers workspace/role activation.
	"""
	if not args:
		return

	selected_modules = []

	# The wizard sends these as checkbox values: aruga_accounting, aruga_payroll
	from aruga_main.modules_registry import ARUGA_MODULES

	for module_def in ARUGA_MODULES:
		if args.get(module_def["module_code"]):
			selected_modules.append(module_def["module_code"])

	if not selected_modules:
		return

	activate_modules(selected_modules)
