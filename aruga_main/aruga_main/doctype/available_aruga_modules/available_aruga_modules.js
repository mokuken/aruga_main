// Copyright (c) 2026, Harly Khen Quimelat and contributors
// For license information, please see license.txt

frappe.ui.form.on("Available ARUGA Modules", {
	refresh(frm) {
		frm.add_custom_button(__("Refresh from Registry"), function () {
			frappe.call({
				method: "aruga_main.install.seed_available_modules",
				freeze: true,
				freeze_message: __("Refreshing module registry..."),
				callback: function () {
					frm.reload_doc();
					frappe.msgprint(__("Module registry refreshed."));
				},
			});
		});
	},
});
