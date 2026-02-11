import frappe

def run():
    workspaces = frappe.get_all("Workspace", fields=["name", "public", "title", "module"])
    print("--- Workspaces ---")
    for w in workspaces:
        print(f"Name: {w.name} | Public: {w.public} | Title: {w.title} | Module: {w.module}")

if __name__ == "__main__":
    frappe.connect("aruga.local")
    run()
