// Copyright (c) 2023, PSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on('BOM Record', {
	refresh: function(frm) {
		frm.fields_dict['items'].grid.get_field('bom_no').get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {    
                filters:[
                    ['item', '=', child.item_code ]
                ]
            }
        }
        frm.set_query('bom', function() {
			return {
				'filters': {
					'is_active': ['=', 1]
				}
			};
		});
        if(!frm.doc.__islocal){
            frm.add_custom_button(__('PSPL BOM Explorer'), function() {
                frappe.route_options = {
                    "bom_record":frm.doc.name
                };
                frappe.set_route("query-report", "PSPL BOM Explorer");
            });
        }
	}
});
frappe.ui.form.on('BOM Record Item', {
	update: function(frm,cdt,cdn) {
		var child = locals[cdt][cdn];
        var delete_items_flag;
        var add_items_flag;
		var refresh_flag;
        frappe.call({
            async:false,
            method: 'pspl_manufacturing.pspl_manufacturing.doctype.bom_record.bom_record.check_bom_status',
            args:{
				//passing item doctype name and item bom
                child_table_name : child.name,
                bom_no : child.bom_no
            },
            callback:(r) => {
                delete_items_flag = r.message
            }
        })

        //if true then deleting items via API
        if(delete_items_flag == true){
            frappe.call({
                async:false,
                method: 'pspl_manufacturing.pspl_manufacturing.doctype.bom_record.bom_record.delete_by_new_bom',
                args:{
                    child_table_name : child.name,
                    item_code : child.item_code,
                    bom_no : child.bom_no,
                    parent_table_name : frm.doc.name,
                    idx : child.idx,
                    bom_level : child.bom_level
                },
                callback:(r) => {
                    add_items_flag = r.message
                }
            })
        }

        //if true then adding items via API
        if(add_items_flag == true){
            frappe.call({
                async:false,
                method: 'pspl_manufacturing.pspl_manufacturing.doctype.bom_record.bom_record.add_by_new_bom',
                args:{
                    child_table_name : child.name,
                    item_code : child.item_code,
                    bom_no : child.bom_no,
                    parent_table_name : frm.doc.name,
                    idx : child.idx,
                    bom_level : child.bom_level
                },
                callback:(r) => {
                    refresh_flag = r.message
                }
            })
        }
            //refresh at the end
            location.reload()
	}
});