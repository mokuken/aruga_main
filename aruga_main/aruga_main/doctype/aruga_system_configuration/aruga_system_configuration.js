// Copyright (c) 2026, Harly Khen Quimelat and contributors
// For license information, please see license.txt

frappe.ui.form.on("ARUGA System Configuration", {
	after_save(frm) {
		frappe.show_alert({
			message: __("Configuration applied. Reloading..."),
			indicator: "green",
		});
		setTimeout(() => {
			window.location.reload();
		}, 1500);
	},

	refresh(frm) {
		// Apply Changes — re-read module workspaces and reapply visibility
		frm.add_custom_button(
			__("Apply Changes"),
			function () {
				frappe.call({
					method: "aruga_main.module_manager.reapply_configuration",
					freeze: true,
					freeze_message: __("Applying module configuration & clearing cache..."),
					callback: function (r) {
						if (r.message && r.message.status === "ok") {
							frappe.show_alert({
								message: __(
									"Configuration applied. Reloading..."
								),
								indicator: "green",
							});
							setTimeout(() => {
								window.location.reload();
							}, 1000);
						}
					},
				});
			},
			__("Actions")
		);

		// Add button to refresh module registry from installed apps
		frm.add_custom_button(
			__("Refresh Module Registry"),
			function () {
				frappe.call({
					method: "aruga_main.install.seed_aruga_modules",
					freeze: true,
					freeze_message: __("Refreshing module registry..."),
					callback: function () {
						frm.reload_doc();
						frappe.msgprint(
							__("Module registry refreshed from installed apps.")
						);
					},
				});
			},
			__("Actions")
		);
	},
});
