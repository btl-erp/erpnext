frappe.ui.form.on("RRCO Receipt Tool", {
	refresh: function(frm) {
		frm.disable_save();
	},
	
	onload: function(frm) {
		frm.set_value("start_date", get_today());
		frm.set_value("end_date", get_today());
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"receipt_date": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"receipt_number": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"tds_rate": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"end_date": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"start_date": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"cheque_date": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	},

	"cheque_no": function(frm) {
		erpnext.rrco_receipt_tool.load_invoices(frm);
	}
});


erpnext.rrco_receipt_tool = {
	load_invoices: function(frm) {
		if(frm.doc.receipt_date && frm.doc.receipt_number && frm.doc.cheque_no && frm.doc.cheque_date) {
			frappe.call({
				method: "erpnext.accounts.doctype.rrco_receipt_tool.rrco_receipt_tool.get_invoices",
				args: {
				   "start_date":frm.doc.start_date,
				   "end_date":frm.doc.end_date,
				   "tds_rate": frm.doc.tds_rate
				},
				callback: function(r) {
					if(r.message['unmarked'].length > 0) {
						unhide_field('unmarked_invoices_section')
						if(!frm.invoice_area) {
							frm.invoice_area = $('<div>')
							.appendTo(frm.fields_dict.invoices_html.wrapper);
						}
						frm.InvoiceSelector = new erpnext.InvoiceSelector(frm, frm.invoice_area, r.message['unmarked'])
					}
					else{
						hide_field('unmarked_invoices_section')
					}

					if(r.message['marked'].length > 0) {
						unhide_field('marked_invoices_section')
						if(!frm.marked_invoice_area) {
							frm.marked_invoice_area = $('<div>')
								.appendTo(frm.fields_dict.marked_attendance_html.wrapper);
						}
						frm.marked_invoice = new erpnext.MarkedInvoice(frm, frm.marked_invoice_area, r.message['marked'])
					}
					else{
						hide_field('marked_invoices_section')
					}
				}
			});
		}
	}
}

erpnext.MarkedInvoice = Class.extend({
	init: function(frm, wrapper, invoice) {
		this.wrapper = wrapper;
		this.frm = frm;
		this.make(frm, invoice);
	},
	make: function(frm, invoice) {
		var me = this;
		$(this.wrapper).empty();

		var row;
		$.each(invoice, function(i, m) {
			var attendance_icon = "icon-check";
			var color_class = "";

			if (i===0 || i % 4===0) {
				row = $('<div class="row"></div>').appendTo(me.wrapper);
			}

			$(repl('<div class="col-sm-3 %(color_class)s">\
				<label class="marked-invoice-label"><span class="%(icon)s"></span>\
				%(invoice)s</label>\
				</div>', {
					invoice: m.invoice_name,
					icon: attendance_icon,
					color_class: color_class
				})).appendTo(row);
		});
	}
});


erpnext.InvoiceSelector = Class.extend({
	init: function(frm, wrapper, invoice) {
		this.wrapper = wrapper;
		this.frm = frm;
		this.make(frm, invoice);
	},
	make: function(frm, invoice) {
		var me = this;

		$(this.wrapper).empty();
		var invoice_toolbar = $('<div class="col-sm-12 top-toolbar">\
			<button class="btn btn-default btn-add btn-xs"></button>\
			<button class="btn btn-xs btn-default btn-remove"></button>\
			</div>').appendTo($(this.wrapper));

		var mark_invoice_toolbar = $('<div class="col-sm-12 bottom-toolbar">\
			<button class="btn btn-primary btn-mark-present btn-xs"></button>\
			<button class="btn btn-default btn-mark-absent btn-xs"></button>\
			<button class="btn btn-default btn-mark-half-day btn-xs"></button></div>')

		invoice_toolbar.find(".btn-add")
			.html(__('Check all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if(!$(check).is(":checked")) {
						check.checked = true;
					}
				});
			});

		invoice_toolbar.find(".btn-remove")
			.html(__('Uncheck all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						check.checked = false;
					}
				});
			});

		mark_invoice_toolbar.find(".btn-mark-present")
			.html(__('Assign Receipt # & Date'))
			.on("click", function() {
				var invoice_present = [];
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						invoice_present.push(invoice[i]);
					}
				});
				frappe.call({
					method: "erpnext.accounts.doctype.rrco_receipt_tool.rrco_receipt_tool.mark_invoice",
					args:{
						"invoice_list":invoice_present,
						"receipt_number":frm.doc.receipt_number,
						"receipt_date":frm.doc.receipt_date,
						"cheque_number":frm.doc.cheque_no,
						"cheque_date":frm.doc.cheque_date,
					},

					callback: function(r) {
						erpnext.rrco_receipt_tool.load_invoices(frm);

					}
				});
			});

		var row;
		$.each(invoice, function(i, m) {
			if (i===0 || (i % 4) === 0) {
				row = $('<div class="row"></div>').appendTo(me.wrapper);
			}
			$(repl('<div class="col-sm-3 unmarked-invoice-checkbox">\
				<div class="checkbox">\
				<label><input type="checkbox" class="invoice-check" invoice="%(invoice)s"/>\
				%(lab_name)s</label>\
				</div></div>', {invoice: m.name, lab_name: m.bill_no})).appendTo(row);
		});

		mark_invoice_toolbar.appendTo($(this.wrapper));
	}
});

