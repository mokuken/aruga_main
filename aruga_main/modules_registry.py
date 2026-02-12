# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Central registry of ARUGA module definitions.

Each entry describes an ARUGA module: its code, human-readable name,
the Frappe app that provides it, the workspaces it controls, etc.

This registry is used to seed ARUGA Module records on install/migrate
and to drive the setup wizard.
"""

ARUGA_MODULES = [
	{
		"module_code": "ARUGA_ACC",
		"module_name": "ARUGA Accounting",
		"description": (
			"Complete accounting solution with BIR reports, financial management, "
			"and Philippine tax compliance"
		),
		"icon": "💰",
		"app_name": "aruga_acct",
		"is_core": 0,
		"order": 1,
		"workspaces": [
			"Accounting",
			"Selling",
			"Buying",
			"Assets",
            "PH Accounting",
		],
	},
	{
		"module_code": "ARUGA_PAY",
		"module_name": "ARUGA Payroll",
		"description": (
			"Payroll processing with SSS, PhilHealth, Pag-IBIG reports "
			"and statutory compliance."
		),
		"icon": "💵",
		"app_name": "aruga_pay",
		"is_core": 0,
		"order": 2,
		"workspaces": [
			"HR",
			"Payroll",
		],
	},
]

# Workspaces that should always remain visible regardless of module selection.
# These are system-level workspaces from Frappe and ERPNext core.
SYSTEM_WORKSPACES = {
	"Home",
	# "Settings",
	# "Users",
	# "Customization",
	# "Build",
	# "Integrations",
	# "Website",
	# "ERPNext Settings",
	# "ERPNext Integrations",
}
