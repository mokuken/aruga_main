# Copyright (c) 2026, Harly Khen Quimelat and contributors
# For license information, please see license.txt

"""
Central registry of ARUGA module definitions.

Each entry maps an ARUGA module to its underlying Frappe app,
the workspaces it exposes, and the roles it requires.
This registry is used to seed the Available ARUGA Modules doctype
and to drive workspace visibility logic.
"""

ARUGA_MODULES = [
	{
		"module_code": "aruga_accounting",
		"module_title": "ARUGA Accounting",
		"description": (
			"Full accounting suite including General Ledger, Accounts Receivable/Payable, "
			"Selling, Buying, Assets, and PH Localization (BIR Reports)."
		),
		"icon": "accounting",
		"app_name": "aruga_acct",
		"display_order": 1,
		"workspaces": [
			"Accounting",
			"Selling",
			"Buying",
			"Assets",
		],
		"roles": [
			"Accounts Manager",
			"Accounts User",
			"Sales Manager",
			"Sales Master Manager",
			"Sales User",
			"Purchase Manager",
			"Purchase User",
			"Item Manager",
			"Stock Manager",
			"Stock User",
		],
	},
	{
		"module_code": "aruga_payroll",
		"module_title": "ARUGA Payroll",
		"description": (
			"HR and Payroll management with PH statutory components "
			"(SSS, PhilHealth, HDMF/Pag-IBIG)."
		),
		"icon": "hr",
		"app_name": "aruga_pay",
		"display_order": 2,
		"workspaces": [
			"HR",
			"Payroll",
		],
		"roles": [
			"HR Manager",
			"HR User",
			"Employee",
		],
	},
]

# Workspaces that should always remain visible regardless of module selection.
# These are system-level workspaces from Frappe and ERPNext core.
SYSTEM_WORKSPACES = {
	# "Home",
	# "Settings",
	# "Users",
	# "Customization",
	# "Build",
	# "Integrations",
	# "Website",
	# "ERPNext Settings",
	# "ERPNext Integrations",
}
