import frappe


def execute():
	"""Remove the ARUGA Configuration Log DocType and its data."""
	# Drop the table if it exists
	if frappe.db.exists("DocType", "ARUGA Configuration Log"):
		frappe.delete_doc_if_exists("DocType", "ARUGA Configuration Log", force=True)

	# Drop table directly in case delete_doc didn't clean it
	frappe.db.sql_ddl("DROP TABLE IF EXISTS `tabARUGA Configuration Log`")
