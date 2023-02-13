// Copyright (c) 2023, PSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on('ROL BOM Item', {
	items_add: function(frm,cdt,cdn) {
		var child = locals[cdt][cdn];
        child.warehouse = cur_frm.doc.p_warehouse;
	}
});
frappe.ui.form.on('ROL BOM', {
	refresh: function(frm) {
		frm.set_query('p_warehouse', function() {
			return {
				'filters': {
					'is_group': ['=', 0],
					'company': ['=', 'Precihole Sports Pvt. Ltd.']
				}
			};
		});
		if(!frm.doc.__islocal){
			frm.add_custom_button(__('PSPL BOM Stock Report'), function() {
				frappe.route_options = {
					"rol_bom" : frm.doc.name
				};
				frappe.set_route("query-report", "PSPL BOM Stock Report");
			});
		}
	}
});