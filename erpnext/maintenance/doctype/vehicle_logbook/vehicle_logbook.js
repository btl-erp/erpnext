// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vehicle Logbook', {
	refresh: function(frm) {
		total_ro = 1
		to_ro = 0
		if (frm.doc.docstatus == 1) {
			total_ro = 0
			to_ro = 1
		}
		cur_frm.set_df_property("total_work_time", "read_only", to_ro);
		cur_frm.set_df_property("distance_km", "read_only", to_ro);
		cur_frm.set_df_property("final_hour", "read_only", to_ro);
		cur_frm.set_df_property("final_km", "read_only", to_ro);
		frappe.meta.get_docfield("Vehicle Log", "distance", cur_frm.doc.name).read_only = 0;
	},
//	"vlogs_on_form_rendered": function(frm, grid_row, cdt, cdn) {
//		var row = cur_frm.open_grid_row();
//		if(!row.grid_form.fields_dict.operator.value) {
//			row.grid_form.fields_dict.operator.set_value(frm.doc.equipment_operator)
  //              	row.grid_form.fields_dict.operator.refresh()
//		}
//	},
	"equipment": function(frm) {
		if(frm.doc.ehf_name && frm.doc.equipment) {
			frappe.call({
				"method": "erpnext.maintenance.doctype.equipment_hiring_form.equipment_hiring_form.get_rates",
				args: {"form": frm.doc.ehf_name, "equipment": frm.doc.equipment},
				callback: function(r) {
					if(r.message) {
						cur_frm.set_value("rate_type", r.message[0].rate_type)
						cur_frm.set_value("work_rate", r.message[0].rate)
						cur_frm.set_value("idle_rate", r.message[0].idle_rate)
						cur_frm.set_value("from_date", r.message[0].from_date)
						cur_frm.set_value("to_date", r.message[0].to_date)
						cur_frm.set_value("from_time", r.message[0].from_time)
						cur_frm.set_value("to_time", r.message[0].to_time)
						cur_frm.set_value("place", r.message[0].place)
						cur_frm.refresh_fields()
					}
				}
			})
			frappe.call({
				"method": "erpnext.maintenance.doctype.equipment.equipment.get_yards",
				args: {"equipment": frm.doc.equipment},
				callback: function(r) {
					if(r.message) {
						cur_frm.set_value("ys_km", r.message[0].kph)
						cur_frm.set_value("ys_hours", r.message[0].lph)
						cur_frm.refresh_fields()
					}
					else {
						msgprint("No yardsticks settings for the equipment")
					}
				}
			})

			get_openings(frm.doc.equipment, frm.doc.from_date, frm.doc.to_date, frm.doc.pol_type)
		}
	},
	"final_km": function(frm) {
		if(!frm.doc.docstatus == 1) {
			calculate_distance_km(frm)
		}
	},
	"initial_km": function(frm) {
		cur_frm.set_value("final_km", parseFloat(frm.doc.initial_km) + parseFloat(frm.doc.distance_km))
		calculate_distance_km(frm)
	},
	//"final_hour": function(frm) {
	//	if(!frm.doc.docstatus == 1) {
	//		calculate_work_hour(frm)
	//	}
	//},
	"initial_hour": function(frm) {
		cur_frm.set_value("final_hour", parseFloat(frm.doc.initial_hour) + parseFloat(frm.doc.total_work_time))
	//	calculate_work_hour(frm)
	},
	"to_date": function(frm) {
		if(frm.doc.from_date > frm.doc.to_date) {
			frappe.msgprint("From Date cannot be greater than To Date")
		}
		else {
			get_openings(frm.doc.equipment, frm.doc.from_date, frm.doc.to_date, frm.doc.pol_type)
		}
	},
	"from_date": function(frm) {
		if(frm.doc.from_date > frm.doc.to_date) {
			frappe.msgprint("From Date cannot be greater than To Date")
		}
		else {
			get_openings(frm.doc.equipment, frm.doc.from_date, frm.doc.to_date, frm.doc.pol_type)
		}
	},
	"total_work_time": function(frm){
		if(frm.doc.total_work_time){
			cur_frm.set_value("final_hour", parseFloat(frm.doc.total_work_time) + parseFloat(frm.doc.initial_hour))
			cur_frm.refresh_fields()
		}

		if(frm.doc.docstatus == 1) {
			calculate_work_hour(frm)
			//cur_frm.set_df_property("total_work_time", "read_only", frm.doc.total_work_time ? 0 : 1);

			cur_frm.refresh_fields()
		}
		if(frm.doc.total_work_time && frm.doc.ys_hours && frm.doc.include_hour) {
			cur_frm.set_value("consumption_hours", frm.doc.total_work_time * frm.doc.ys_hours)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},
	"distance_km": function(frm) {
		if(frm.doc.distance_km){
			cur_frm.set_value("final_km", flt(frm.doc.distance_km) + flt(frm.doc.initial_km))
			cur_frm.refresh_fields()
		}
		if(frm.doc.docstatus == 1) {
			calculate_distance_km(frm)
			cur_frm.refresh_fields()
		}
		if(frm.doc.distance_km && frm.doc.ys_km && frm.doc.include_km) {
			cur_frm.set_value("consumption_km", frm.doc.distance_km / frm.doc.ys_km)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},

	"include_hour": function(frm) {
		if(!frm.doc.include_hour) {
			cur_frm.set_value("consumption_hours", 0)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
		if(frm.doc.total_work_time && frm.doc.ys_hours && frm.doc.include_hour) {
			cur_frm.set_value("consumption_hours", frm.doc.total_work_time * frm.doc.ys_hours)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},

	"include_km": function(frm) {
		if(!frm.doc.include_km) {
			cur_frm.set_value("consumption_km", 0)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	
		if(frm.doc.distance_km && frm.doc.ys_km && frm.doc.include_km) {
			cur_frm.set_value("consumption_km", frm.doc.distance_km / frm.doc.ys_km)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},
	
	"other_consumption": function(frm) {
		if(!frm.doc.other_consumption) {
			cur_frm.set_value("other_consumption", 0)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
		}
		if(frm.doc.other_consumption) {
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},
	opening_balance: function(frm) {
		calculate_closing(frm)
	},

	hsd_received: function(frm) {
		calculate_closing(frm)
	},

	consumption_hours: function(frm) {
		if(frm.doc.total_work_time && frm.doc.ys_hours && frm.doc.include_hour) {
			frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_field("consumption")
			calculate_closing(frm)
		}
	},

	consumption: function(frm) {
		calculate_closing(frm)
	}
});

function calculate_closing(frm) {
	frm.set_value("closing_balance", frm.doc.hsd_received + frm.doc.opening_balance - frm.doc.consumption)
	cur_frm.refresh_field("closing_balance")
}

function calculate_distance_km(frm) {
	if(frm.doc.docstatus == 0) {
		if(flt(frm.doc.final_km) > flt(frm.doc.initial_km)) {
			cur_frm.set_value("distance_km", flt(frm.doc.final_km) - flt(frm.doc.initial_km))
			frm.refresh_fields()
		}
		else {
			cur_frm.set_value("distance_km", "0")
			frm.refresh_fields()
			if(frm.doc.final_km) {
				frappe.msgprint("Final KM should be greater than Initial KM")
			}
		}
	}
	if(frm.doc.docstatus == 1) {
		cur_frm.set_value("final_km", flt(frm.doc.distance_km) + flt(frm.doc.initial_km))
		cur_frm.refresh_fields()
	}
}

function calculate_work_hour(frm) {
	if(frm.doc.docstatus == 0) {
		if(flt(frm.doc.final_hour) > flt(frm.doc.initial_hour)) {
			cur_frm.set_value("total_work_time", flt(frm.doc.final_hour) - flt(frm.doc.initial_hour))
			frm.refresh_fields()
		}
		else {
			cur_frm.set_value("total_work_time", "0")
			frm.refresh_fields()
			if(frm.doc.final_hour) {
				frappe.msgprint("Final Hour should be greater than Initial Hour")
			}
		}
	}
	if(frm.doc.docstatus == 1 ) {
		cur_frm.set_value("final_hour", flt(frm.doc.total_work_time) + flt(frm.doc.initial_hour))
		cur_frm.refresh_fields()
	}
}


cur_frm.add_fetch("equipment", "equipment_number", "equipment_number")
cur_frm.add_fetch("equipment", "hsd_type", "pol_type")
cur_frm.add_fetch("equipment", "current_operator", "equipment_operator")
cur_frm.add_fetch("operator", "employee_name", "driver_name")

//Vehicle Log Item  Details
frappe.ui.form.on("Vehicle Log", {
	//"vlogs_add": function(frm, cdt, cdn){
        //      var cur = locals[cdt][cdn];
          ///      var vlogs = frm.doc.vlogs || [];
             //   if(vlogs[parseInt(vlogs.length)-2] === undefined){
               //         frappe.model.set_value(cdt, cdn, "work_date", frm.doc.from_date);
             //   }
               // else {
                 //       if(vlogs[parseInt(vlogs.length)-2].work_date){
                   //             frappe.model.set_value(cdt, cdn, "work_date", frappe.datetime.add_days(vlogs[parseInt(vlogs.length)-2].work_date,1));
                   //     }
               // }
       // },

	"work_date": function(frm, cdt, cdn) {
		date_check(frm, cdt, cdn)
	},

	"from_time": function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"to_time": function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"from_km_reading": function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"to_km_reading": function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"idle_time": function(frm, cdt, cdn) {
		check(frm, cdt, cdn)
		total_time(frm, cdt, cdn)
		//cur_frm.field_dict.vlogs.grid.toggle_reqd("idle_time", 1)
	},
	"work_time": function(frm, cdt, cdn) {
		check(frm, cdt, cdn)
		total_time(frm, cdt, cdn)
        },
	"qty_cft": function(frm, cdt, cdn) {
		check(frm, cdt, cdn)
		total_time(frm, cdt, cdn)
        },
	"distance": function(frm, cdt, cdn) {
		check(frm, cdt, cdn)
		total_time(frm, cdt, cdn)
		//if (!distance){
		//frappe.model.set_value(cdt, cdn, "distance", 0)}
	},
})
function check(frm,cdt, cdn){
	var a = locals[cdt][cdn]
		if(a.idle_time && a.idle_time < 0 || a.idle_time > 24){
                        frappe.msgprint ("Idle Time cannot be negative nor it can be more then 24 hours")
                }
                if(a.work_time && a.work_time < 0 || a.work_time > 24){
                        frappe.msgprint("Work Time cannot be negative nor it can be more then 24 hours")
		}
		if(a.distance && a.distance < 0){
			frappe.msgprint("Distance cannot be negative")
                }
	}

function date_check(frm, cdt, cdn){
	var a = locals[cdt][cdn]
		console.log(a.work_date)
		if (a.work_date && a.work_date < frm.doc.from_date || a.work_date > frm.doc.to_date){
			frappe.model.set_value(cdt, cdn, "work_date", "" )
			frappe.msgprint ("Work Date must be between From Date and To Date")
		
	}
		frm.doc.vlogs.forEach(function(d){
			if (a.name != d.name && d.work_date == a.work_date){
				frappe.model.set_value(cdt, cdn,"work_date", "")
				frappe.msgprint ("Cannot have VLB entry for same date")
			}
		});
	
	}	

function get_openings(equipment, from_date, to_date, pol_type) {
	if (equipment && from_date && to_date && pol_type) {
		frappe.call({
			"method": "erpnext.maintenance.doctype.vehicle_logbook.vehicle_logbook.get_opening",
			args: {"equipment": equipment, "from_date": from_date, "to_date": to_date, "pol_type": pol_type},
			callback: function(r) {
				if(r.message) {
					cur_frm.set_value("opening_balance", r.message[0])
					cur_frm.set_value("hsd_received", r.message[3])
					cur_frm.set_value("initial_km", r.message[1])
					cur_frm.set_value("initial_hour", r.message[2])
					cur_frm.refresh_fields()
				}
			}
		})
	}
}

function total_time(frm, cdt, cdn) {
	var total_idle = total_work = total_distance = total_cft = 0;
	frm.doc.vlogs.forEach(function(d) {
		if(d.idle_time) { 
			total_idle += flt(d.idle_time)
		}
		if(d.work_time) {
			total_work += flt(d.work_time)
		}
		if(d.distance){
			total_distance += flt(d.distance)
		}
		if(d.qty_cft){
			total_cft += flt(d.qty_cft)
		}
	
	})
	frm.set_value("total_idle_time", total_idle)
	frm.set_value("total_work_time", total_work)
	frm.set_value("distance_km", total_distance)
	frm.set_value("total_cft", total_cft)
	cur_frm.refresh_field("total_work_time")
	cur_frm.refresh_field("total_idle_time")
	cur_frm.refresh_field("distance_km")
	cur_frm.refresh_field("total_cft")
}

function calculate_time(frm, cdt, cdn) {
	var item = locals[cdt][cdn]
	if(item.from_time && item.to_time && item.to_time >= item.from_time) {
		frappe.model.set_value(cdt, cdn,"time", frappe.datetime.get_hour_diff(Date.parse("2/12/2016"+' '+item.to_time), Date.parse("2/12/2016"+' '+item.from_time)))
	}
	cur_frm.refresh_field("time")
}

function calculate_distance(frm, cdt, cdn) {
	var item = locals[cdt][cdn]
	if(item.from_km_reading && item.to_km_reading && item.to_km_reading >= item.from_km_reading) {
		frappe.model.set_value(cdt, cdn,"distance", item.to_km_reading - item.from_km_reading)
	}
	cur_frm.refresh_field("distance")
}

frappe.ui.form.on("Vehicle Logbook", "refresh", function(frm) {
    cur_frm.set_query("ehf_name", function() {
        return {
            "filters": {
                "payment_completed": 0,
		"docstatus": 1,
		"branch": frm.doc.branch
            }
        };
    });

    cur_frm.set_query("equipment", function() {
        return {
	    query: "erpnext.maintenance.doctype.equipment.equipment.get_equipments",
            "filters": {
                "ehf_name": frm.doc.ehf_name,
            }
        };
    });
	
});
