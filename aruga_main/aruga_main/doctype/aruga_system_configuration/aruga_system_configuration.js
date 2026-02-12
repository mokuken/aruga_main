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
		// Add button to populate from available ARUGA Module records
		frm.add_custom_button(__("Add Module"), function () {
			const existing = (frm.doc.enabled_modules || []).map(
				(row) => row.module
			);

			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "ARUGA Module",
					fields: ["name", "module_name", "is_core", "app_name"],
					order_by: "`order` asc",
					limit_page_length: 0,
				},
				callback: function (r) {
					const all_modules = r.message || [];
					const available = all_modules.filter(
						(m) => !existing.includes(m.name)
					);

					if (!available.length) {
						frappe.msgprint(
							__("All available modules are already in the list.")
						);
						return;
					}

					frappe.prompt(
						{
							fieldname: "module",
							fieldtype: "Link",
							label: __("Select Module"),
							options: "ARUGA Module",
							reqd: 1,
							get_query: function () {
								return {
									filters: {
										name: ["not in", existing],
									},
								};
							},
						},
						function (values) {
							const row = frm.add_child("enabled_modules");
							row.module = values.module;
							row.enabled = 1;
							frm.refresh_field("enabled_modules");
							frm.dirty();
						},
						__("Add ARUGA Module"),
						__("Add")
					);
				},
			});
		});

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

		// Add button to view configuration history
		frm.add_custom_button(
			__("View Change Log"),
			function () {
				frappe.set_route("List", "ARUGA Configuration Log");
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
