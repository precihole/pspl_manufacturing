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
        frm.add_custom_button(__('PSPL BOM Explorer'), function() {
            frappe.route_options = {
                "bom_record":frm.doc.name
            };
            frappe.set_route("query-report", "PSPL BOM Explorer");
        });
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
            method: 'pspl_manufacturing.pspl_manufacturing.doctype.bom_record.bom_record.chk_bom_change_status',
            args:{
				//passing item doctype name and item bom
                item_name : child.name,
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
                method: 'pspl_manufacturing.pspl_manufacturing.doctype.bom_record.bom_record.delete_items_based_on_new_bom',
                args:{
                    item_name : child.name,
                    item_code : child.item_code,
                    bom_no : child.bom_no,
                    docname : frm.doc.name,
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
                method: 'pspl_manufacturing.pspl_manufacturing.doctype.bom_record.bom_record.add_items_based_on_new_bom',
                args:{
                    item_name : child.name,
                    item_code : child.item_code,
                    bom_no : child.bom_no,
                    docname : frm.doc.name,
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