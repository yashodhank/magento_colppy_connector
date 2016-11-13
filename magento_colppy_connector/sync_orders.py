from __future__ import unicode_literals
import frappe
from frappe import _
from .exceptions import MeliError
from .utils import make_meli_log
from .sync_products import make_item
from .sync_customers import create_customer, create_customer_address, create_customer_contact, change_shipping_address
from frappe.utils import flt, nowdate, cint
from .meli_requests import get_request, get_meli_orders
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note, make_sales_invoice

# def sync_orders():
# 	sync_meli_orders()
#
# def sync_meli_orders():
# 	frappe.local.form_dict.count_dict["orders"] = 0
# 	meli_settings = frappe.get_doc("Meli Settings", "Meli Settings")
#
# 	for meli_order in get_meli_orders():
# 		if valid_customer_and_product(meli_order):
# 			try:
# 				create_order(meli_order, meli_settings)
# 				frappe.local.form_dict.count_dict["orders"] += 1
#
# 			except MeliError, e:
# 				make_meli_log(status="Error", method="sync_meli_orders", message=frappe.get_traceback(),
# 					request_data=meli_order, exception=True)
# 			except Exception, e:
# 				if e.args[0] and e.args[0].startswith("402"):
# 					raise e
# 				else:
# 					make_meli_log(title=e.message, status="Error", method="sync_meli_orders", message=frappe.get_traceback(),
# 						request_data=meli_order, exception=True)

def webhook_meli_orders(meli_order):
	# frappe.local.form_dict.count_dict["orders"] = 0
	meli_settings = frappe.get_doc("Meli Settings", "Meli Settings")

	if valid_customer_and_product(meli_order):
		# try:
		create_order(meli_order, meli_settings)
		# frappe.local.form_dict.count_dict["orders"] += 1

		# except MeliError, e:
		# 	make_meli_log(status="Error", method="sync_meli_orders", message=frappe.get_traceback(),
		# 		request_data=meli_order, exception=True)
		# except Exception, e:
		# 	if e.args[0] and e.args[0].startswith("402"):
		# 		raise e
		# 	else:
		# 		make_meli_log(title=e.message, status="Error", method="sync_meli_orders", message=frappe.get_traceback(),
		# 			request_data=meli_order, exception=True)
def valid_customer_and_product(meli_order):

	# shipping_status = meli_order.get("shipping").get("status")
	# ME1 & ME2: to_be_agreed / pending / handling / ready_to_ship / shipped / delivered / not_delivered / cancelled
	# shipping_mode = meli_order.get("shipping").get("shipping_mode") if "shipping_mode" in meli_order.get("shipping") else None
	# me1 / me2 / custom
	# free_shipping = meli_order.get("shipping").get("free_shipping") if "free_shipping" in meli_order.get("shipping") else None
	# True / None
	shipping = False if meli_order.get("shipping").get("status") == "to_be_agreed" else True
	paid = True if meli_order.get("status") == "paid" else False
	buyer = meli_order.get("buyer")
	erp_customer = frappe.db.get_value(doctype="Customer",
										filters={"meli_customer_id": buyer.get("id")},
										fieldname=["name"],
										as_dict=1)

	if not erp_customer:
		erp_customer = create_customer(buyer, meli_order)

	if shipping:
		receiver_address = meli_order.get("shipping").get("receiver_address")

		erp_address = frappe.db.get_values(doctype="Address",
											filters={"meli_address_id": receiver_address.get("id")},
											fieldname=["name", "is_shipping_address"],
											as_dict=1)

		make_meli_log(title="ERP Adress", status="Error", method="valid_customer_and_product", message=frappe.get_traceback(),
			request_data=erp_address, exception=True)

		if not erp_address:
			create_customer_address(erp_customer, meli_order.get("shipping"), receiver_address.get("id"))
		else:
			change_shipping_address(erp_address)

		contact_fullname = buyer.get("first_name") + " " + buyer.get("last_name") if "last_name" in buyer else buyer.get("first_name")
		contact_name = str(contact_fullname) + "-" + erp_customer.name

		if paid:
			erp_contact = frappe.db.get_value(doctype="Contact",
												filters={"name": contact_name},
												fieldname=["name"])

			make_meli_log(title="ERP Contact", status="Error", method="sync_meli_orders", message=frappe.get_traceback(),
				request_data=str(buyer.get("first_name")) + "-" + erp_customer.name, exception=True)

			if not erp_contact:
				create_customer_contact(erp_customer, meli_order, buyer, receiver_address)

	# else:
	# 	raise _("Customer is mandatory to create order")

	warehouse = frappe.get_doc("Meli Settings", "Meli Settings").warehouse

	for item in meli_order.get("order_items"):
		if not frappe.db.get_value("Item", {"meli_product_id": item.get("item").get("id")}, "name"):
			item = get_request("/items/{0}".format(item.get("item").get("id")))
			make_item(warehouse, item, meli_item_list=[])

	return True

def create_order(meli_order, meli_settings, company=None):
	so = create_sales_order(meli_order, meli_settings, company)

	if meli_order.get("status") == "paid" and cint(meli_settings.sync_sales_invoice):
		create_sales_invoice(meli_order, meli_settings, so)

	if "id" in meli_order.get("shipping") and\
	meli_order.get("status") == "paid" and\
	cint(meli_settings.sync_delivery_note):
		create_delivery_note(meli_order, meli_settings, so)

	return so

def create_sales_order(meli_order, meli_settings, company=None):

	if meli_order.get("shipping").get("shipping_mode", {}) == "me2":
		shipping_method = "Mercado Envios"
		shipping_cost = meli_order.get("shipping").get("cost")
	elif meli_order.get("shipping").get("status") == "to_be_agreed":
		shipping_method = "Retira"
		shipping_cost = 0

	so = frappe.db.get_value("Sales Order", {"meli_order_id": meli_order.get("id")}, "name")

	if not so:
		so = frappe.get_doc({
			"doctype": "Sales Order",
			"naming_series": meli_settings.sales_order_series or "SO-Meli-",
			"meli_order_id": meli_order.get("id"),
			"customer": frappe.db.get_value("Customer", {"meli_customer_id": meli_order.get("buyer").get("id")}, "name"),
			"delivery_date": nowdate(),
			"selling_price_list": meli_settings.price_list,
			"ignore_pricing_rule": 1,
			"items": get_order_items(meli_order.get("order_items"), meli_settings),
			"meli_order_status": get_meli_order_status(meli_order),
			"meli_payment_type": get_meli_payment_type(meli_order),
			"meli_payment_installments": meli_order.get("payments")[0].get("installments"),
			"meli_payment_status": get_meli_payment_status(meli_order),
			"taxes": [{
				"charge_type": _("Actual"),
				"account_head": get_tax_account_head(shipping_method),
				"description": meli_order.get("shipping").get("name") or "",
				"tax_amount": shipping_cost
			}]
		})

		# "taxes": get_order_taxes(meli_order, meli_settings)
		# "apply_discount_on": "Grand Total"
		# "discount_amount": get_discounted_amount(meli_order),

		if company:
			so.update({
				"company": company,
				"status": "Draft"
			})
		so.flags.ignore_mandatory = True
		so.save(ignore_permissions=True)
		so.submit()

	else:
		so = frappe.get_doc("Sales Order", so)

	frappe.db.commit()
	return so

# def get_meli_label():
# 	if meli_order.get("shipping").get("status") == "ready_to_ship":
# 		so["meli_label"] = get_request("/shipment_labels?shipment_ids={0}&response_type=pdf".format(meli_order.get("shipment").get("id")))

def get_meli_payment_type(meli_order):
	payment_types = {
		"credit_card": "Tarjetas de credito",
		"atm": "Transferencia bancaria",
		"ticket": "Efectivo"
	}

	for payment_type in meli_order.get("payments"):
		meli_payment_type = payment_types.get(payment_type.get("payment_type"))

	return meli_payment_type

def get_meli_payment_status(meli_order):
	payment_status = {
		"approved": "Aprobado",
		"pending": "Pendiente",
		"rejected": "Rechazado"
	}

	meli_payment_status = meli_order.get("payments")[0].get("status")
	return payment_status.get(meli_payment_status)

def get_meli_order_status(meli_order):
	order_status = {
		"confirmed": "Confirmado",
		"payment_required": "Requiere Pago",
		"payment_in_process": "Pago en Proceso",
		"partially_paid": "Pago Parcial",
		"paid": "Pagado",
		"cancelled": "Cancelado",
		"invalid": "Invalido"
	}

	meli_order_status = meli_order.get("status")
	return order_status.get(meli_order_status)

def create_sales_invoice(meli_order, meli_settings, so):
	if not frappe.db.get_value("Sales Invoice", {"meli_order_id": meli_order.get("id")}, "name")\
		and so.docstatus==1 and not so.per_billed:
		si = make_sales_invoice(so.name)
		si.meli_order_id = meli_order.get("id")
		si.naming_series = meli_settings.sales_invoice_series or "SI-Meli-"
		si.is_pos = 0
		si.cash_bank_account = meli_settings.cash_bank_account
		si.flags.ignore_mandatory = True
		si.submit()
		frappe.db.commit()

		# De esta manera solo se puede realizar el pago una sola vez, no se
		# contempla sobrepagos ni pagos parciales. RESOLVER!
		meli_payment = meli_order.get("payments")[0]
		payment = frappe.get_doc({
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"party_name": meli_order.get("buyer").get("name"),
			"party_type": "Customer",
			"party": meli_order.get("buyer").get("nickname"),
			"title": meli_order.get("buyer").get("name"),
			"paid_amount": meli_payment.get("transaction_amount") + meli_payment.get("shipping_cost"),
			"paid_to": meli_settings.cash_bank_account,
			"reference_no": meli_payment.get("id"),
			"reference_date": meli_payment.get("date_last_modified"),
			"received_amount": meli_payment.get("total_paid_amount"),
			"mode_of_payment": get_meli_payment_type(meli_order),
			"method_of_payment": meli_payment.get("payment_method_id"),
			"status_of_payment": get_meli_payment_status(meli_order),
			"references": [
				{
					"reference_doctype": "Sales Invoice",
					"total_amount": meli_payment.get("transaction_amount") + meli_payment.get("shipping_cost"),
					"reference_name": si.name,
					"allocated_amount": meli_payment.get("transaction_amount") + meli_payment.get("shipping_cost"),
				}
			]
		})

		payment.insert()
		payment.flags.ignore_mandatory = True
		payment.submit()
		frappe.db.commit()

def create_delivery_note(meli_order, meli_settings, so):
	delivery_note = frappe.db.get_value(doctype="Delivery Note",
										filters={"meli_fulfillment_id": meli_order.get("shipping").get("id")},
										filedname=["name", "customer"],
										as_dict=1)
	if not delivery_note and so.docstatus==1:
		dn = make_delivery_note(so.name)
		dn.meli_order_id = meli_order.get("id")
		dn.meli_fulfillment_id = meli_order.get("shipping").get("id"),
		dn.naming_series = meli_settings.delivery_note_series or "DN-Meli-"
		# dn.items = get_fulfillment_items(dn.items, shipping.get("line_items"), meli_settings)
		dn.flags.ignore_mandatory = True
		dn.save()
		frappe.db.commit()

	else:
		default_address = frappe.db.get_value(doctype="Address",
											filters={"customer": delivery_note.get("name"),
													"is_shipping_address": 1},
											fieldname=["name"])

		modif_delivery_note = frappe.get_doc("Delivery Note", delivery_note)
		modif_delivery_note.shipping_address_name = default_address
		modif_delivery_note.save()
		frappe.db.commit()


# def get_fulfillment_items(dn_items, fulfillment_items, meli_settings):
# 	return [dn_item.update({"qty": item.get("quantity")}) for item in fulfillment_items for dn_item in dn_items\
# 			if get_item_code(item) == dn_item.item_code]

# def get_discounted_amount(order):
# 	discounted_amount = 0.0
# 	for discount in order.get("discount_codes"):
# 		discounted_amount += flt(discount.get("amount"))
# 	return discounted_amount

def get_order_items(order_items, meli_settings):
	items = []
	for meli_item in order_items:
		item_code = get_item_code(meli_item)
		items.append({
			"item_code": item_code,
			"item_name": meli_item.get("item").get("title"),
			"rate": meli_item.get("unit_price"),
			"qty": meli_item.get("quantity"),
			"warehouse": meli_settings.warehouse
		})
		# "stock_uom": meli_item.get("sku"),
	return items

def get_item_code(meli_item):
	item_code = frappe.db.get_value("Item", {"meli_variant_id": meli_item.get("item").get("variation_id")}, "item_code")
	if not item_code:
		item_code = frappe.db.get_value("Item", {"meli_product_id": meli_item.get("item").get("id")}, "item_code")

	return item_code

# def get_order_taxes(meli_order, meli_settings):
# 	taxes = []
# 	for tax in meli_order.get("tax_lines"):
# 		taxes.append({
# 			"charge_type": _("On Net Total"),
# 			"account_head": get_tax_account_head(tax),
# 			"description": "{0} - {1}%".format(tax.get("title"), tax.get("rate") * 100.0),
# 			"rate": tax.get("rate") * 100.00,
# 			"included_in_print_rate": 1 if meli_order.get("taxes_included") else 0
# 		})
#
# 	taxes = update_taxes_with_shipping_lines(taxes, meli_order.get("shipping_lines"))
#
# 	return taxes
#
# def update_taxes_with_shipping_lines(taxes, shipping_lines):
# 	for shipping_charge in shipping_lines:
# 		taxes.append({
# 			"charge_type": _("Actual"),
# 			"account_head": get_tax_account_head(shipping_charge),
# 			"description": shipping_charge["title"],
# 			"tax_amount": shipping_charge["price"]
# 		})
#
# 	return taxes
#
def get_tax_account_head(tax):
	tax_account =  frappe.db.get_value("Meli Tax Account", \
		{"parent": "Meli Settings", "meli_tax": tax}, "tax_account")

	if not tax_account:
		frappe.throw("Tax Account not specified for Meli Tax {}".format(tax.get("title")))

	return tax_account
