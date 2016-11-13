import frappe
from meli_connector.meli_requests import get_meli_orders, get_request
from frappe.utils import cstr
from frappe import _

def execute():
	meli_settings = frappe.db.get_value("Meli Settings", None,
		["enable_meli", "meli_url"], as_dict=1)

	if not (meli_settings and meli_settings.enable_meli and meli_settings.meli_url):
		return

	try:
		meli_orders = get_meli_orders(ignore_filter_conditions=True)
		meli_orders = build_meli_order_dict(meli_orders, key="id")
	except:
		return

	for so in frappe.db.sql("""select name, meli_order_id, discount_amount from `tabSales Order`
		where meli_order_id is not null and meli_order_id != '' and
		docstatus=1 and discount_amount > 0""", as_dict=1):

		try:
			meli_order = meli_orders.get(so.meli_order_id) or {}

			if so.meli_order_id not in meli_orders:
				meli_order = get_request("/orders".format(so.meli_order_id))["order"]

			if meli_order.get("taxes_included"):
				so = frappe.get_doc("Sales Order", so.name)

				setup_inclusive_taxes(so, meli_order)
				so.calculate_taxes_and_totals()
				so.set_total_in_words()
				db_update(so)

				update_si_against_so(so, meli_order)
				update_dn_against_so(so, meli_order)

				frappe.db.commit()
		except Exception:
			pass

def setup_inclusive_taxes(doc, meli_order):
	doc.apply_discount_on = "Grand Total"
	meli_taxes = get_meli_tax_settigns(meli_order)

	for tax in doc.taxes:
		if tax.account_head in meli_taxes:
			tax.charge_type = _("On Net Total")
			tax.included_in_print_rate = 1
#
def update_si_against_so(so, meli_order):
	si_name =frappe.db.sql_list("""select distinct t1.name
		from `tabSales Invoice` t1,`tabSales Invoice Item` t2
		where t1.name = t2.parent and t2.sales_order = %s and t1.docstatus = 1""", so.name)

	if si_name:
		si = frappe.get_doc("Sales Invoice", si_name[0])

		si.docstatus = 2
		si.update_prevdoc_status()
		si.make_gl_entries_on_cancel()

		si.docstatus = 1
		setup_inclusive_taxes(si, meli_order)
		si.calculate_taxes_and_totals()
		si.set_total_in_words()
		si.update_prevdoc_status()
		si.make_gl_entries()

		db_update(si)

def update_dn_against_so(so, meli_order):
	dn_name =frappe.db.sql_list("""select distinct t1.name
		from `tabDelivery Note` t1,`tabdelivery Note Item` t2
		where t1.name = t2.parent and t2.against_sales_order = %s and t1.docstatus = 0""", so.name)

	if dn_name:
		dn = frappe.get_doc("Delivery Note", dn_name[0])

		setup_inclusive_taxes(dn, meli_order)
		dn.calculate_taxes_and_totals()
		dn.set_total_in_words()

		db_update(dn)

def db_update(doc):
	doc.db_update()
	for df in doc.meta.get_table_fields():
		for d in doc.get(df.fieldname):
			d.db_update()

def build_meli_order_dict(sequence, key):
	return dict((cstr(d[key]), dict(d, index=index)) for (index, d) in enumerate(sequence))

def get_meli_tax_settigns(meli_order):
	meli_taxes = []
	for tax in meli_order.get("tax_lines"):
		meli_taxes.extend(map(lambda d: d.tax_account if d.meli_tax == tax["title"] else "", frappe.get_doc("Meli Settings").taxes))

	return set(meli_taxes)
