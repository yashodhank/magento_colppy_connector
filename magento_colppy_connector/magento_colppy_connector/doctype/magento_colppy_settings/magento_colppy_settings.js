// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("magento_colppy_connector.magento_colppy_settings");
frappe.provide("erpnext.item");

frappe.ui.form.on("Magento Colppy Settings", "onload", function(frm, dt, dn){
	frappe.call({
		method:"magento_colppy_connector.magento_colppy_connector.doctype.magento_colppy_settings.magento_colppy_settings.get_series",
		callback:function(r){
			$.each(r.message, function(key, value){
				set_field_options(key, value)
			})
		}
	})
	magento_colppy_connector.magento_colppy_settings.setup_queries(frm);
})

// frappe.ui.form.on("Magento Colppy Settings", "app_type", function(frm, dt, dn) {
// 	frm.toggle_reqd("client_id", (frm.doc.app_type == "Private"));
// 	frm.toggle_reqd("password", (frm.doc.app_type == "Private"));
// })

frappe.ui.form.on("Magento Colppy Settings", "refresh", function(frm){
	if(!frm.doc.__islocal && frm.doc.enable_magento_colppy === 1){
		frm.toggle_reqd("price_list", true);
		frm.toggle_reqd("warehouse", true);
		frm.toggle_reqd("taxes", true);
		frm.toggle_reqd("cash_bank_account", true);
		frm.toggle_reqd("sales_order_series", true);
		frm.toggle_reqd("customer_group", true);

		frm.toggle_reqd("sales_invoice_series", frm.doc.sync_sales_invoice);
		frm.toggle_reqd("delivery_note_series", frm.doc.sync_delivery_note);

		cur_frm.add_custom_button(__("Sync MercadoLibre"),
			function() {
				frappe.call({
					method:"magento_colppy_connector.api.sync_magento_colppy",
				})
			}, 'icon-sitemap')
	}


	cur_frm.add_custom_button(__("Connect to MercadoLibre"),
		function(){
			window.open("https://" + frm.doc.company + ".binar.io/api/method/magento_colppy_connector.magento_colppy_requests.redirect_access_token", "_self");
		}).addClass("btn-primary")

	cur_frm.add_custom_button(__("Magento Colppy Log"), function(){
		frappe.set_route("List", "Magento Colppy Log");
	})


	frappe.call({
		method: "magento_colppy_connector.api.get_log_status",
		callback: function(r) {
			if(r.message){
				frm.dashboard.set_headline_alert(r.message.text, r.message.alert_class)
			}
		}
	})

})

frappe.ui.form.on("Item", "magento_colppy_prediction_button",
    function(frm) {
        frappe.call({
            "method": "magento_colppy_connector.magento_colppy_connector.sync_products.predict_category",
            args: {
                doctype: "Item"
            }
        })
    });


$.extend(magento_colppy_connector.magento_colppy_settings, {
	setup_queries: function(frm) {
		frm.fields_dict["warehouse"].get_query = function(doc) {
			return {
				filters:{
					"company": doc.company,
					"is_group": "No"
				}
			}
		}

		frm.fields_dict["taxes"].grid.get_field("tax_account").get_query = function(doc, dt, dn){
			return {
				"query": "erpnext.controllers.queries.tax_account_query",
				"filters": {
					"account_type": ["Tax", "Chargeable", "Expense Account"],
					"company": frappe.defaults.get_default("Company")
				}
			}
		}

		frm.fields_dict["cash_bank_account"].get_query = function(doc) {
			return {
				filters: [
					["Account", "account_type", "in", ["Cash", "Bank"]],
					["Account", "root_type", "=", "Asset"],
					["Account", "is_group", "=",0],
					["Account", "company", "=", doc.company]
				]
			}
		}
	}
})
