/**
 * ARUGA Main — Desk Router Override
 *
 * Overrides Frappe's default logo-click / "/app" navigation so that
 * instead of trying to show a "Home" workspace (which ARUGA removes),
 * it redirects to the first visible workspace from the user's enabled modules.
 *
 * Priority:
 *   1. User's default_workspace (set on the User doctype)
 *   2. First public, non-hidden, top-level workspace from allowed_workspaces
 *   3. Any remaining workspace as last fallback
 *
 * This file is loaded via app_include_js in hooks.py, so it is automatically
 * active when aruga_main is installed and removed when it is uninstalled.
 */

$(document).ready(function () {
	if (!frappe.router) return;

	// ── Override render() ───────────────────────────────────────────────
	// Stock Frappe calls frappe.views.pageview.show("") when the route is
	// empty (i.e. navigating to /app). That tries to show a "Home" page.
	// We intercept that and redirect to the first available workspace.
	const _original_render = frappe.router.render;

	frappe.router.render = function () {
		if (this.current_route[0]) {
			// Normal page — use stock behaviour
			this.render_page();
		} else {
			// Empty route (/app) — go to first workspace
			let ws = aruga_get_first_workspace();
			if (ws) {
				frappe.route_flags.replace_route = true;
				let slug = frappe.router.slug(
					ws.public ? ws.title : "private/" + ws.title
				);
				frappe.set_route(slug);
			} else {
				// Nothing available — fall back to stock
				_original_render.call(this);
			}
		}
	};

	// ── Override make_url() ─────────────────────────────────────────────
	// This is used to resolve <a href="/app"> links (like the navbar logo).
	// When params produce an empty path, stock Frappe looks for a "home"
	// workspace. We redirect to the first enabled workspace instead.
	const _original_make_url = frappe.router.make_url;

	frappe.router.make_url = function (params) {
		let path_string = $.map(params, function (a) {
			if ($.isPlainObject(a)) {
				frappe.route_options = a;
				return null;
			} else {
				return encodeURIComponent(String(a));
			}
		}).join("/");

		if (path_string) {
			return "/app/" + path_string;
		}

		// Empty path — resolve to first workspace
		let ws = aruga_get_first_workspace();
		if (ws) {
			return (
				"/app/" +
				(ws.public ? "" : "private/") +
				frappe.router.slug(ws.title)
			);
		}

		// Fallback to stock resolution
		return _original_make_url.call(this, params);
	};
});

/**
 * Determine the first workspace the current user should land on.
 *
 * @returns {Object|null}  { title, public } or null
 */
function aruga_get_first_workspace() {
	// 1. User's explicitly configured default workspace
	if (frappe.boot.user && frappe.boot.user.default_workspace) {
		return {
			title: frappe.boot.user.default_workspace.title || frappe.boot.user.default_workspace.name,
			public: frappe.boot.user.default_workspace.public ?? true,
		};
	}

	// 2. First public, non-hidden, top-level workspace from the
	//    (already module-filtered) allowed_workspaces list
	let workspaces = frappe.boot.allowed_workspaces || [];
	let visible = workspaces.filter(
		(ws) => ws.public && !ws.is_hidden && !ws.parent_page
	);

	if (visible.length) return visible[0];

	// 3. Any workspace at all
	if (workspaces.length) return workspaces[0];

	return null;
}
