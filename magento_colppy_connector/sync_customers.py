from __future__ import unicode_literals
import frappe
from frappe import _
import requests.exceptions
from .magento_colppy_requests import post_request, put_request
from .utils import make_meli_log

# from .meli_requests import get_meli_customers, post_request, put_request

# def sync_customers():
# 	meli_customer_list = []
# 	# sync_meli_customers(meli_customer_list)
# 	frappe.local.form_dict.count_dict["customers"] = len(meli_customer_list)

	# sync_erpnext_customers(meli_customer_list)

# def sync_meli_customers(meli_customer_list):
# 	for meli_customer in get_meli_customers():
# 		if not frappe.db.get_value("Customer", {"meli_customer_id": meli_customer.get('id')}, "name"):
# 			create_customer(meli_customer, meli_customer_list)

def create_customer(meli_customer, meli_order):
	meli_settings = frappe.get_doc("Meli Settings", "Meli Settings")

	# cust_name = (meli_customer.get("first_name") + " " + (meli_customer.get("last_name") \
	# 	and  meli_customer.get("last_name") or "")) if meli_customer.get("first_name")\
	# 	else meli_customer.get("email")

	# try:
	customer = frappe.get_doc({
		"doctype": "Customer",
		"name": meli_customer.get("nickname"),
		"customer_name" : meli_customer.get("nickname"),
		"meli_customer_id": meli_customer.get("id"),
		"sync_with_meli": 1,
		"customer_group": meli_settings.customer_group,
		"territory": frappe.utils.nestedset.get_root_of("Territory"),
		"customer_type": _("Individual")
	})

	customer.flags.ignore_mandatory = True
	customer.flags.ignore_permissions = True
	customer.insert()
	frappe.db.commit()

	return customer

	# except Exception, e:
	# 	if e.args[0] and e.args[0].startswith("402"):
	# 		raise e
	# 	else:
	# 		make_meli_log(title=e.message, status="Error", method="create_customer", message=frappe.get_traceback(),
	# 			request_data=meli_customer, exception=True)

def create_customer_address(customer, meli_shipping, receiver_address_id):
	receiver_address = meli_shipping.get("receiver_address")

	# erp_id_address = frappe.db.get_value(doctype="Address",
	# 									filters={"meli_address_id": receiver_address.get("id")},
	# 									fieldname="name")
	#
	# if not erp_id_address:
	address_title, address_type = get_address_title_and_type(customer.get("name"), receiver_address_id)
	# try:
	address = frappe.get_doc({
		"doctype": "Address",
		"meli_address_id": receiver_address.get("id"),
		"address_title": address_title,
		"address_type": address_type,
		"address_line1": receiver_address.get("street_name") + " " + receiver_address.get("street_number"),
		"address_line2": receiver_address.get("comment"),
		"city": receiver_address.get("city").get("name"),
		"state": receiver_address.get("state").get("name"),
		"pincode": receiver_address.get("zip_code"),
		"country": receiver_address.get("country").get("name"),
		"phone": receiver_address.get("receiver_phone"),
		"customer": customer.get("name"),
		"customer_name":  customer.get("name"),
		"is_shipping_address": 1
	})

	address.flags.ignore_mandatory = True
	address.flags.ignore_permissions = True
	address.insert()
	frappe.db.commit()

	# except Exception, e:
	# 	make_meli_log(title=e.message, status="Error", method="create_customer_address", message=frappe.get_traceback(),
	# 		request_data=meli_shipping, exception=True)

def get_address_title_and_type(customer_name, receiver_address_id):
	address_type = "Shipping"
	address_title = "{0}-{1}".format(customer_name, receiver_address_id)

	if frappe.db.get_value("Address", "{0}-{1}".format(customer_name.strip(), address_type)):
		address_title = "{0}-{1}".format(customer_name.strip(), receiver_address_id)

	return address_title, address_type

def change_shipping_address(erp_address):
	for address in erp_address:
		doc_address = frappe.get_doc("Address", address["name"])

		if address["is_shipping_address"] == 1:
			doc_address.is_shipping_address = 0
		elif address["is_shipping_address"] == 0:
			doc_address.is_shipping_address = 1

		doc_address.flags.ignore_permissions = True
		doc_address.save()

def	create_customer_contact(customer, meli_order, buyer, receiver_address):
	# erp_id_contact = frappe.db.get_value(doctype="Contact",
	# 									filters={"customer": customer.get("name")},
	# 									fieldname="name")
	#
	# if not erp_id_contact:
	phone = buyer.get("phone")
	buyer_phone = "(" + phone.get("area_code") + ") " + phone.get("number") + " | " + phone.get("extension")

	contact = frappe.get_doc({
		"doctype": "Contact",
		"customer": customer.get("name"),
		"customer_name": customer.get("name"),
		"first_name": buyer.get("first_name") or receiver_address.get("receiver_name"),
		"last_name": buyer.get("last_name"),
		"phone": buyer_phone,
		"email_id": buyer.get("email"),
		"is_primary_contact": 1
	})

	contact.flags.ignore_mandatory = True
	contact.flags.ignore_permissions = True
	contact.insert()
	frappe.db.commit()

# def sync_erpnext_customers(meli_customer_list):
# 	meli_settings = frappe.get_doc("Meli Settings", "Meli Settings")
#
# 	condition = ["sync_with_meli = 1"]
#
# 	last_sync_condition = ""
# 	if meli_settings.last_sync_datetime:
# 		last_sync_condition = "modified >= '{0}' ".format(meli_settings.last_sync_datetime)
# 		condition.append(last_sync_condition)
#
# 	customer_query = """select name, customer_name, meli_customer_id from tabCustomer
# 		where {0}""".format(" and ".join(condition))
#
# 	for customer in frappe.db.sql(customer_query, as_dict=1):
# 		try:
# 			if not customer.meli_customer_id:
# 				create_customer_to_meli(customer)
#
# 			else:
# 				if customer.meli_customer_id not in meli_customer_list:
# 					update_customer_to_meli(customer, last_sync_condition)
#
# 			frappe.local.form_dict.count_dict["customers"] += 1
# 			frappe.db.commit()
# 		except Exception, e:
# 			make_meli_log(title=e.message, status="Error", method="sync_erpnext_customers", message=frappe.get_traceback(),
# 				request_data=customer, exception=True)
#
# def create_customer_to_meli(customer):
# 	meli_customer = {
# 		"first_name": customer['customer_name'],
# 	}
#
# 	meli_customer = post_request("/admin/customers.json", { "customer": meli_customer})
#
# 	customer = frappe.get_doc("Customer", customer['name'])
# 	customer.meli_customer_id = meli_customer['customer'].get("id")
#
# 	customer.flags.ignore_mandatory = True
# 	customer.save()
#
# 	addresses = get_customer_addresses(customer.as_dict())
# 	for address in addresses:
# 		sync_customer_address(customer, address)
#
# def sync_customer_address(customer, address):
# 	address_name = address.pop("name")
#
# 	meli_address = post_request("/admin/customers/{0}/addresses.json".format(customer.meli_customer_id),
# 	{"address": address})
#
# 	address = frappe.get_doc("Address", address_name)
# 	address.meli_address_id = meli_address['customer_address'].get("id")
# 	address.save()
#
# def update_customer_to_meli(customer, last_sync_condition):
# 	meli_customer = {
# 		"first_name": customer['customer_name'],
# 		"last_name": ""
# 	}
#
# 	try:
# 		put_request("/admin/customers/{0}.json".format(customer.meli_customer_id),\
# 			{ "customer": meli_customer})
# 		update_address_details(customer, last_sync_condition)
#
# 	except requests.exceptions.HTTPError, e:
# 		if e.args[0] and e.args[0].startswith("404"):
# 			customer = frappe.get_doc("Customer", customer.name)
# 			customer.meli_customer_id = ""
# 			customer.sync_with_meli = 0
# 			customer.flags.ignore_mandatory = True
# 			customer.save()
# 		else:
# 			raise
#
# def update_address_details(customer, last_sync_condition):
# 	customer_addresses = get_customer_addresses(customer, last_sync_condition)
# 	for address in customer_addresses:
# 		if address.meli_address_id:
# 			url = "/admin/customers/{0}/addresses/{1}.json".format(customer.meli_customer_id,\
# 			address.meli_address_id)
#
# 			address["id"] = address["meli_address_id"]
#
# 			del address["meli_address_id"]
#
# 			put_request(url, { "address": address})
#
# 		else:
# 			sync_customer_address(customer, address)
#
# def get_customer_addresses(customer, last_sync_cond=None):
# 	conditions = ["addr.customer = '{0}' ".format(customer['name'])]
#
# 	if last_sync_cond:
# 		conditions.append(last_sync_cond)
#
# 	address_query = """select addr.name, addr.address_line1 as address1, addr.address_line2 as address2,
# 		addr.city as city, addr.state as province, addr.country as country, addr.pincode as zip,
# 		addr.meli_address_id from tabAddress addr
# 		where {0}""".format(' and '.join(conditions))
#
# 	return frappe.db.sql(address_query, as_dict=1)
