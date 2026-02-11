// Copyright (c) 2026, Harly Khen Quimelat and contributors
// For license information, please see license.txt

/**
 * ARUGA Module Selection — Setup Wizard Slide
 *
 * This file is loaded during the Frappe Setup Wizard via the
 * setup_wizard_requires hook. It adds a "Module Selection" slide
 * that appears BEFORE the ERPNext "Organization" slide.
 *
 * The slide presents the available ARUGA modules as checkboxes
 * and lets the admin pick which modules to activate.
 */

frappe.setup.on("before_load", function () {
	// Skip if aruga_main setup has already been completed
	if (
		frappe.boot.setup_wizard_completed_apps &&
		frappe.boot.setup_wizard_completed_apps.length &&
		frappe.boot.setup_wizard_completed_apps.includes("aruga_main")
	) {
		return;
	}

	frappe.setup.add_slide(aruga_module_selection_slide);
});

const aruga_module_selection_slide = {
	name: "aruga_module_selection",
	title: __("Welcome to ARUGA"),
	icon: "fa fa-th-large",
	fields: [
		{
			fieldtype: "HTML",
			fieldname: "module_selection_description",
			options: `
				<div class="aruga-module-selection-header" style="margin-bottom: 24px;">
					<p style="font-size: 14px; color: var(--text-muted);">
						${__("Choose which ARUGA modules to enable. You can change this later from ARUGA System Configuration.")}
					</p>
					<p style="font-size: 13px; color: var(--text-light);">
						${__("Select at least one module to continue.")}
					</p>
				</div>
			`,
		},
		{
			fieldtype: "Section Break",
			label: __("Available Modules"),
		},
		{
			fieldname: "aruga_accounting",
			label: __("ARUGA Accounting"),
			fieldtype: "Check",
			description: __(
				"Full accounting suite: General Ledger, AR/AP, Selling, Buying, Assets, and PH Localization (BIR Reports)."
			),
		},
		{
			fieldtype: "Column Break",
		},
		{
			fieldname: "aruga_payroll",
			label: __("ARUGA Payroll"),
			fieldtype: "Check",
			description: __(
				"HR and Payroll management with PH statutory components (SSS, PhilHealth, HDMF/Pag-IBIG)."
			),
		},
	],

	onload: function (slide) {
		// Fetch available modules from server to check which apps are installed
		frappe.call({
			method: "aruga_main.module_manager.get_available_modules",
			async: false,
			callback: function (r) {
				if (r.message) {
					const available_codes = r.message.map((m) => m.module_code);

					// Disable checkboxes for modules whose apps aren't installed
					["aruga_accounting", "aruga_payroll"].forEach((code) => {
						const field = slide.form.fields_dict[code];
						if (field && !available_codes.includes(code)) {
							field.$wrapper.find("input").prop("disabled", true);
							field.$wrapper
								.find(".checkbox-label, label")
								.css("opacity", "0.5");
							field.set_description(
								__("This module's app is not installed in this container.")
							);
						}
					});
				}
			},
		});
	},

	validate: function () {
		const values = this.values;
		if (!values.aruga_accounting && !values.aruga_payroll) {
			frappe.msgprint({
				title: __("Selection Required"),
				indicator: "orange",
				message: __("Please select at least one ARUGA module to continue."),
			});
			return false;
		}
		return true;
	},
};
