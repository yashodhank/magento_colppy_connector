from __future__ import unicode_literals
import frappe
from .meli_requests import post_request, put_request
from .sync_products import make_item

def meli_validations(doc, method):
    meli_settings = frappe.get_doc("Meli Settings")
    item_price = frappe.db.get_value("Item Price",
                                    {"item_code": doc.name,
                                    "price_list": meli_settings.price_list},
                                    ["price_list_rate", "price_list"],
                                    as_dict=1)

    item_stock = frappe.db.get_value("Bin",
                                    {"item_code": doc.name,
                                    "warehouse": meli_settings.warehouse},
                                    ["actual_qty", "warehouse"],
                                    as_dict=1)

    item_stock_msg = ""
    item_price_msg = ""
    item_status_msg = ""

    if doc.sync_with_meli == True:
            if not item_stock or item_stock["actual_qty"] == 0:
                item_stock_msg = "<br />Faltan cantidades en el deposito <strong>{0}</strong><br />".format(meli_settings.warehouse.upper())

            if not item_price or item_price["price_list_rate"] == 0:
                item_price_msg = "<br />Falta precio en la lista <strong>{0}</strong><br />".format(meli_settings.price_list.upper())

            if doc.meli_actual_status == "Finalizado" and doc.meli_status != "Activar":
                item_status_msg = "<br />Este articulo se encuentra <strong>FINALIZADO</strong>.<br />"

    if item_stock_msg != "" or item_price_msg  != "" or item_status_msg  != "":
        frappe.msgprint("<div style='text-align: center;'><h1>Errores en MercadoLibre Sync</h1> \
                        <h3>Se deshabilito la sincronizacion con MercadoLibre</h3> \
                        <br /> \
                        {0}{1}{2} \
                        </div>".format(item_stock_msg, item_price_msg, item_status_msg),
                        "Alerta de Sincronizacion", indicator="red")
        disable_meli_sync_for_item(doc, True)
    else:
        change_status(doc, method, item_price, item_stock)


def change_status(doc, method, item_price, item_stock):
    meli_settings = frappe.get_doc("Meli Settings", "Meli Settings")
    warehouse = meli_settings.warehouse
    meli_item_list = []

    if doc.meli_product_id != "No Sync":
        if doc.meli_actual_status == "Activo" and doc.meli_status == "Pausar":
            put_request("/items/{0}".format(doc.meli_product_id), {"status": "paused"})
            doc.meli_actual_status = "Pausado"
            doc.meli_status = "Seleccione una Opcion"

        elif doc.meli_actual_status == "Activo" and doc.meli_status == "Finalizar":
            put_request("/items/{0}".format(doc.meli_product_id), {"status": "closed"})
            doc.meli_actual_status = "Finalizado"
            doc.meli_status = "Seleccione una Opcion"
            doc.disabled = 1

        elif doc.meli_actual_status == "Pausado" and doc.meli_status == "Activar":
            put_request("/items/{0}".format(doc.meli_product_id), {"status": "active"})
            doc.meli_actual_status = "Activo"
            doc.meli_status = "Seleccione una Opcion"

        elif doc.meli_actual_status == "Pausado" and doc.meli_status == "Finalizar":
            put_request("/items/{0}".format(doc.meli_product_id), {"status": "closed"})
            doc.meli_actual_status = "Finalizado"
            doc.meli_status = "Seleccione una Opcion"
            doc.disabled = 1

        elif doc.meli_actual_status == "Finalizado" and doc.meli_status == "Activar":
            data_relist = {
                            "price": item_price.price_list_rate if hasattr(item_price, "price_list_rate") and item_price.price_list_rate > 0 else 1,
                            "quantity": item_stock.actual_qty if hasattr(item_stock, "actual_qty") and item_stock.actual_qty > 0 else 1,
                            "listing_type_id": get_listing_type_id(doc.listing_type_id)
                            }
            meli_item = post_request("/items/{0}/relist".format(doc.meli_product_id), data_relist)
            make_item(warehouse, meli_item, meli_item_list)
            # doc.meli_actual_status = "Activo"
            doc.meli_status = "Seleccione una Opcion"
            # doc.meli_product_id = r.get("id")
            # doc.meli_variant_id = r.get("id")
            # doc.item_code = r.get("id")
            frappe.db.commit()

def get_listing_type_id(listing_type):
    listing_type_id = frappe.db.get_value("Meli Listing Type", {"name": listing_type}, ["id_listing_type"])

    return listing_type_id

def disable_meli_sync_for_item(item, rollback=False):
	"""Disable Item if not exist on MercadoLibre"""
	if rollback:
		frappe.db.rollback()

	item.sync_with_meli= 0
	# item.sync_qty_with_meli = 0
	# item.save(ignore_permissions=True)
	frappe.db.commit()

# "price": frappe.db.get_value("Item Price", {"item_code": doc.item_code, "price_list": meli_settings.price_list}, "price_list_rate"),
# "quantity": frappe.db.get_value("Bin", {"item_code": doc.item_code, "warehouse": meli_settings.warehouse}, "actual_qty"),
# "listing_type_id": doc.listing_type_id
