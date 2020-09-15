// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee', 'salutation', 'salutation');
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');
cur_frm.add_fetch('employee', 'employment_type', 'employment_type');
cur_frm.add_fetch('employee', 'employee_group', 'employee_group');
cur_frm.add_fetch('employee', 'employee_subgroup', 'employee_grade');
cur_frm.add_fetch('employee', 'designation', 'designation');
cur_frm.add_fetch('employee', 'branch', 'employee_branch');

frappe.ui.form.on('Other Contribution', {
	setup: function(frm) {
		frm.get_docfield("items").allow_bulk_edit = 1;
		frm.get_field('items').grid.editable_fields = [
				{fieldname: 'employee', columns: 3},
				{fieldname: 'employee_grade', columns: 1},
				{fieldname: 'designation', columns: 2},
				{fieldname: 'branch', columns: 2},
				{fieldname: 'contribution', columns: 2},
		];
	},
	onload: function(frm){
		employee_details(frm);
		total_html(frm);
		if(frm.doc.__islocal){
			update_data(frm.doc, "remove_employee");
		}
	},
	refresh: function(frm) {
		cur_frm.set_query("group_cost_center", function() {
                return {
                    "filters": {
                        "is_disabled": 0,
                        "list_in_other_contribution": 1
                    }
                };
        });
		employee_details(frm);
		total_html(frm);
	},
	employee: function(frm){
		employee_details(frm);
		//update_data(frm.doc, "remove_employee");
	},
	get_employees: function(frm) {
		update_data(frm.doc, "get_employees");
	},
	contribution_type: function(frm){
		update_data(frm.doc, "update_amounts");
	},
	contribution: function(frm){
		update_data(frm.doc, "update_amounts");
	},
	total_contribution_amount: function(){
		total_html(frm);
	}
});

var update_data=function(doc, method){
	cur_frm.call({
		method: method,
		doc:doc
	});
}

var employee_details = function(frm){
	if(frm.doc.employee){
		$(cur_frm.fields_dict.employee_details.wrapper).html("<b>"+(frm.doc.salutation ? frm.doc.salutation+". " : frm.doc.salutation)+frm.doc.employee_name+"<br>"+frm.doc.designation+" ("+frm.doc.employee_grade+")"+"<br>"+'<a href="/desk#Form/Branch/'+frm.doc.employee_branch+'">'+frm.doc.employee_branch+"</a>"+"</b>");
	} else {
		$(cur_frm.fields_dict.employee_details.wrapper).html('');
	}
}

var total_html = function(frm){
	if(frm.doc.total_contribution_amount > 0){
		$(cur_frm.fields_dict.total_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Total No.of Contributors</label><br><b>'+frm.doc.total_noof_contributors+"/"+frm.doc.total_noof_employees+'</b>');
	} else {
		$(cur_frm.fields_dict.total_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Total No.of Contributors</label><br><b>'+'</b>');
	}
}