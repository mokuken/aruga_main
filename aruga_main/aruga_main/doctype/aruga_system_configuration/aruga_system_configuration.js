// Copyright (c) 2026, Harly Khen Quimelat and contributors
// For license information, please see license.txt

frappe.ui.form.on("ARUGA System Configuration", {
	refresh(frm) {
		// Add a button to add modules from the registry
		frm.add_custom_button(__("Add Module from Registry"), function () {
			frappe.call({
				method: "aruga_main.module_manager.get_available_modules",
				callback: function (r) {
					if (!r.message || !r.message.length) {
						frappe.msgprint(__("No ARUGA modules available in this container."));
						return;
					}

					const existing_codes = (frm.doc.selected_modules || []).map(
						(row) => row.module_code
					);
					const available = r.message.filter(
						(m) => !existing_codes.includes(m.module_code)
					);

					if (!available.length) {
						frappe.msgprint(__("All available modules are already selected."));
						return;
					}

					const options = available.map((m) => m.module_title);
					frappe.prompt(
						{
							fieldname: "module",
							fieldtype: "Select",
							label: __("Select Module"),
							options: options.join("\n"),
							reqd: 1,
						},
						function (values) {
							const selected = available.find(
								(m) => m.module_title === values.module
							);
							if (selected) {
								const row = frm.add_child("selected_modules");
								row.module_code = selected.module_code;
								row.module_title = selected.module_title;
								frm.refresh_field("selected_modules");
								frm.dirty();
							}
						},
						__("Add ARUGA Module"),
						__("Add")
					);
				},
			});
		});
	},
});
