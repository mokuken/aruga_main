// Copyright (c) 2026, Harly Khen Quimelat and contributors
// For license information, please see license.txt

frappe.ui.form.on("ARUGA Module", {
	refresh(frm) {
		// Show active status indicator
		if (frm.doc.is_active) {
			frm.page.set_indicator(__("Active"), "green");
		} else {
			frm.page.set_indicator(__("Inactive"), "orange");
		}

		// Prevent disabling core modules via is_active (read-only anyway)
		if (frm.doc.is_core) {
			frm.set_intro(
				__("This is a core module and cannot be disabled."),
				"blue"
			);
		}

		// Add button to quickly add workspaces
		frm.add_custom_button(__("Add Workspace"), function () {
			const existing = (frm.doc.module_workspaces || []).map(
				(row) => row.workspace
			);
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Workspace",
					filters: { public: 1, for_user: "" },
					fields: ["name", "title"],
					limit_page_length: 0,
				},
				callback: function (r) {
					const workspaces = (r.message || []).filter(
						(ws) => !existing.includes(ws.name)
					);

					if (!workspaces.length) {
						frappe.msgprint(
							__("All public workspaces are already added.")
						);
						return;
					}

					const options = workspaces.map((ws) => ws.name);
					frappe.prompt(
						{
							fieldname: "workspace",
							fieldtype: "Link",
							label: __("Workspace"),
							options: "Workspace",
							reqd: 1,
							get_query: function () {
								return {
									filters: {
										public: 1,
										name: ["not in", existing],
									},
								};
							},
						},
						function (values) {
							const row = frm.add_child("module_workspaces");
							row.workspace = values.workspace;
							row.visible = 1;
							row.order =
								(frm.doc.module_workspaces || []).length;
							frm.refresh_field("module_workspaces");
							frm.dirty();
						},
						__("Add Workspace"),
						__("Add")
					);
				},
			});
		});
	},
});
