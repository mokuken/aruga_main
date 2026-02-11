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

	// Fetch all modules synchronously
	let all_modules = [];
	frappe.call({
		method: "aruga_main.module_manager.get_all_modules",
		async: false,
		callback: function (r) {
			all_modules = r.message || [];
		},
	});

	if (all_modules.length) {
		const fields = [
			{
				fieldtype: "HTML",
				fieldname: "module_ui",
			},
		];

		all_modules.forEach((m) => {
			fields.push({
				fieldname: m.module_code,
				fieldtype: "Check",
				hidden: 1,
				default: m.installed ? 1 : 0,
			});
		});

		aruga_module_selection_slide.fields = fields;
		aruga_module_selection_slide._all_modules = all_modules;

		frappe.setup.slides.splice(
			frappe.setup.slides.findIndex((slide) => slide.name === "welcome") + 1,
			0,
			aruga_module_selection_slide
		);
	}
});

const aruga_module_selection_slide = {
	name: "aruga_module_selection",
	title: __("Welcome to ARUGA"),
	icon: "fa fa-th-large",
	// fields populated dynamically above

	onload: function (slide) {
		const modules = slide._all_modules || [];
		const get_field = (name) => slide.form.fields_dict[name];

		const cards_html = modules
			.map((m) => {
				const is_disabled = !m.installed;
				const icon_content = (m.icon && m.icon.startsWith("fa-")) 
					? `<i class="fa ${m.icon}"></i>` 
					: (m.icon || `<i class="fa fa-cube"></i>`);
				
				return `
					<div class="aruga-card ${is_disabled ? "disabled" : ""}" data-module="${
					m.module_code
				}" ${is_disabled ? 'title="' + __("App not installed") + '"' : ""}>
						<div class="check-icon"><i class="fa fa-check-square"></i></div>
						<div class="aruga-icon-box ${m.module_code}">${icon_content}</div>
						<div class="aruga-card-content">
							<div class="aruga-card-title">${__(m.module_title)}</div>
							<div class="aruga-card-desc">${__(m.description)}</div>
						</div>
					</div>
				`;
			})
			.join("");

		const html = `
			<style>
				.aruga-module-container {
					text-align: center;
					margin-top: 30px;
					max-width: 500px;
					margin-left: auto;
					margin-right: auto;
				}
				.aruga-module-title {
					font-size: 22px;
					font-weight: 700;
					margin-bottom: 40px;
					color: var(--text-color);
				}
				.aruga-cards {
					display: flex;
					flex-direction: column;
					justify-content: center;
					gap: 20px;
				}
				.aruga-card {
					background: var(--card-bg, #fff);
					border: 1px solid var(--border-color, #e2e6eb);
					border-radius: 8px;
					padding: 20px;
					width: 100%;
					cursor: pointer;
					position: relative;
					transition: all 0.2s ease;
					box-shadow: 0 1px 3px rgba(0,0,0,0.05); /* Thin shadow */
					display: flex;
					flex-direction: row;
					align-items: center;
					text-align: left;
				}
				.aruga-card:hover {
					box-shadow: 0 10px 20px rgba(0,0,0,0.08); /* A bit more lift on hover */
					transform: translateY(-2px);
				}
				.aruga-card.selected {
					border-color: transparent;
					box-shadow: 0 0 0 2px var(--primary-color, #2490ef);
				}
				.aruga-card.disabled {
					opacity: 0.6;
					pointer-events: none;
					filter: grayscale(1);
				}
				.aruga-card .check-icon {
					position: absolute;
					top: 10px;
					right: 10px;
					color: var(--primary-color, #2490ef);
					display: none;
					font-size: 16px;
				}
				.aruga-card.selected .check-icon {
					display: block;
				}
				.aruga-icon-box {
					width: 48px;
					height: 48px;
					margin-right: 20px;
					margin-bottom: 0;
					display: flex;
					align-items: center;
					justify-content: center;
					font-size: 42px;
					flex-shrink: 0;
				}
				.aruga-card-content {
					flex: 1;
				}
				.aruga-card-title {
					font-weight: bold;
					font-size: 16px;
					margin-bottom: 4px;
					color: var(--text-color);
				}
				.aruga-card-desc {
					font-size: 13px;
					color: var(--text-muted);
					line-height: 1.5;
				}
			</style>
			<div class="aruga-module-container">
				<div class="aruga-module-title">${__("Which module do you want to work with?")}</div>
				<div class="aruga-cards">
					${cards_html}
				</div>
			</div>
		`;

		slide.get_field("module_ui").$wrapper.html(html);

		const update_card = (module) => {
			const field = get_field(module);
			if (!field) return;

			const is_checked = field.get_value();
			const $card = slide
				.get_field("module_ui")
				.$wrapper.find(`.aruga-card[data-module="${module}"]`);
			if (is_checked) {
				$card.addClass("selected");
			} else {
				$card.removeClass("selected");
			}
		};

		// Init UI
		modules.forEach((m) => update_card(m.module_code));

		// Click events
		slide
			.get_field("module_ui")
			.$wrapper.on("click", ".aruga-card", function () {
				if ($(this).hasClass("disabled")) return;
				const module = $(this).data("module");
				const field = get_field(module);
				const new_val = field.get_value() ? 0 : 1;

				field.set_input(new_val);
				update_card(module);
			});
	},

	validate: function () {
		const values = this.values;
		let any_selected = false;
		if (this._all_modules) {
			this._all_modules.forEach((m) => {
				if (values[m.module_code]) any_selected = true;
			});
		}

		if (!any_selected) {
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
