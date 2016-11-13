from __future__ import unicode_literals
import frappe
from frappe import _
import requests.exceptions
from .exceptions import MeliError
from .utils import make_magento_log, disable_magento_sync_for_item, is_magento_enabled
from erpnext.stock.utils import get_bin
from frappe.utils import cstr, flt, cint, get_files_path
from .magento_colppy_requests import get_request, post_request, get_magento_items, put_request,\
	 put_images, delete_request, get_prediction_resource, get_attributes, get_variation_picture
import requests
from datetime import datetime, timedelta

"""
/// El conector sincroniza directamente un ERP con un Servicio ///
"""

def sync_products(price_list, warehouse, magento_item_list):
	sync_magento_items(warehouse, magento_item_list)
	frappe.local.form_dict.count_dict["products"] = len(magento_item_list)
	sync_erp_items(price_list, warehouse, magento_item_list)


"""/////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////
////////////////////// Ecommerce --> Conector //////////////////////////
////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////"""


def sync_magento_items(warehouse, magento_item_list):
	for magento_item in get_magento_items():
		try:
			make_item(warehouse, magento_item, magento_item_list)
		except MeliError, e:
			make_magento_log(title=e.message, status="Error", method="sync_magento_items", message=frappe.get_traceback(),
				request_data=magento_item, exception=True)

		# except Exception, e:
		# 	if e.args[0] and e.args[0].startswith("404"):
		# 		raise e
		# 	else:
		# 		make_magento_log(title=e.message, status="Error", method="sync_magento_items", message=frappe.get_traceback(),
		# 			request_data=magento_item, exception=True)


def make_item(warehouse, magento_item, magento_item_list):
	# # Items con variantes
	# # (Reemplazar por el llamado a las variaciones del Ecommerce)
	# if len(magento_item.get("variations")) >= 1:
	# 	attributes = create_attribute(magento_item)
	# 	create_item(magento_item, warehouse, 1, attributes, magento_item_list=magento_item_list)
	# 	create_item_variants(magento_item, warehouse, attributes, magento_item_list=magento_item_list)
	#
	# #Items simples
	# else:
	magento_item["variant_id"] = "No Variations"
	create_item(magento_item, warehouse, magento_item_list=magento_item_list)


# No aplica en el caso de Colppy/Contabilium
# def create_attribute(magento_item):
# 	attribute = []
# 	# (Reemplazar por el llamado a las variaciones del Ecommerce)
# 	attributes_categories = get_attributes(magento_item.get("category_id"))
#
# 	try:
# 		for attr in attributes_categories:
# 			# Los atributos no pueden ser "hidden" ni "fixed"
# 			if "hidden" not in attr.get("tags") and "fixed" not in attr.get("tags"):
# 				# Verifica que el atributo no exista en el ERP
# 				if not frappe.db.get_value("Item Attribute", attr.get("name"), "name"):
# 					# Crea un "Item Attribute"
# 					# (Agregar un POST al ERP si tiene Variaciones)
# 					frappe.get_doc({
# 						"doctype": "Item Attribute",
# 						"attribute_name": "MELI" + attr.get("name"),
# 						"item_attribute_values": [
# 							{
# 								"attribute_value": attr_value["name"] + " (" + attr_value["id"] + ")",
# 								"abbr": attr_value["name"] + " (" + attr_value["id"] + ")"
# 							}
# 							for attr_value in attr.get("values")
# 						]
# 					}).insert()
#
# 					# Crea una variante N/A de cada atributo de la cateogria porque
# 					# el ERP necesita llenar todos los atributos cuando crea una variante
# 					# (Agregar un POST al ERP si tiene variaciones)
# 					frappe.get_doc({
# 						"doctype": "Item Attribute Value",
# 						"parenttype": "Item Attribute",
# 						"parentfield": "item_attribute_values",
# 						"parent": attr.get("name"),
# 						"attribute_value": "N/A",
# 						"abbr": "N/A"
# 					}).insert()
#
# 					# crea una lista de diccionarios con los atributos creados
# 					attribute.append({"attribute": attr.get("name")})
#
# 				else:
# 					# Trae todos los datos del atributo en cuestion
# 					item_attr = frappe.get_doc("Item Attribute", attr.get("name"))
# 					# Verifica que no sea del tipo "Talle"
# 					if not item_attr.numeric_values:
# 						# Agrega los nuevos atributos
# 						set_new_attribute_values(item_attr, attr.get("values"))
# 						item_attr.flags.ignore_permissions = True
# 						# (Aregar un PUT al ERP)
# 						item_attr.save()
# 						# crea una lista de diccionarios con los atributos creados
# 						attribute.append({"attribute": attr.get("name")})
#
# 	except Exception, e:
# 		make_magento_log(title=e.message, status="Error", exception=True)
#
# 	return attribute
# 	# attrbute = [
# 	# 	{"attribute": "Nombre del atributo 1"},
# 	# 	{"attribute": "Nombre del atributo 2"},
# 	# 	{"attribute": "Nombre del atributo 3"}
# 	# ]


# No aplica en el caso de Colppy/Contabilium
# def set_new_attribute_values(item_attr, values):
# 	for attr_value in values:
# 		if not any((d.abbr.lower() == attr_value["name"].lower() or d.attribute_value.lower() == attr_value["name"].lower())\
# 		for d in item_attr.item_attribute_values):
# 			# (Reemplazar por el diccionario que necesite el ERP)
# 			item_attr.append("item_attribute_values", {
# 				"attribute_value": attr_value["name"],
# 				"abbr": attr_value["name"]
# 			})


def create_item(magento_item, warehouse, has_variant=0, attributes=None, variant_of=None, magento_item_list=[]):
	colppy_magento_settings = frappe.get_doc("Meli Magento Settings")

	# Se emparejan las keys del ERP con las del Ecommerce
	item_dict = {
		"idEmpresa": colppy_magento_settings.id_empresa,
		"codigo": magento_item.get("id"),
		"descripcion": magento_item.get("name"),
		"unidadMedida": """Unidad de Medida de Magento""",
		"detalle": magento_item.get("name"),
		"ctaCostoVentas": colppy_magento_settings.cta_costo_ventas or "511100",
        "ctaIngresoVentas": colppy_magento_settings.cta_ingreso_ventas or "410100",
        "ctaInventario": colppy_magento_settings.cta_inventario or "115100",
		"iva": "21",
        "tipoItem": "P"
	}

	# Trae las imagenes en el caso de productos simples y variables
	# No aplica en el caso de Colppy/Contabilium
	# aux_item_dict_images(item_dict, magento_item, variant_of)

	# (Agregar un diccionario con las key del ERP/Ecommerce para hacer despues el POST/PUT correspondiente)

	try:
		# Verifica si el Item existe y la temporalidad de la modificacion
		if not is_item_exists(item_dict, magento_item, attributes, magento_item_list=magento_item_list):
			# Verifica que tenga los campos basicos para poder agregarse al ERP
			item_details = get_item_details(item_dict)

			if not item_details:
				# Crea un nuevo Item
				# new_item = frappe.get_doc(item_dict)
				# new_item.flags.ignore_permissions = True
				# new_item.insert()
				post_request("Inventario", "alta_iteminventario", item_dict)
			else:
				# update_item(item_details, item_dict)
				post_request("Inventario", "editar_iteminventario", item_dict)

			if not has_variant:
				add_to_price_list(magento_item, item_dict["codigo"])

		# No aplica en Colppy/Contabilium
		# Sin esta funcion no guarda los cambios en la base de datos
		# frappe.db.commit()

	except Exception, e:
		make_magento_log(title=e.message, status="Error", exception=True)


# # No aplica en el caso de Colppy/Contabilium
# def create_item_variants(magento_item, warehouse, attributes, magento_item_list):
#
# 	template_item = frappe.db.get_value(doctype="Item",
# 										filters={"name": magento_item.get("id")},
# 										fieldname=["name", "magento_product_id"],
# 										as_dict=True)
# 	template_item_attrib = frappe.db.get_values(doctype="Item Variant Attribute",
# 												filters={"parent": template_item.name},
# 												fieldname=["attribute"])
#
# 	if template_item:
# 		for variation in magento_item.get("variations"):
#
# 			magento_item_variant = {
# 				"variant_title": magento_item.get("title"),
# 				"magento_variant_id": variation.get("id"),
# 				"variant_item_price": variation.get("price"),
# 				"sold_quantity": variation.get("sold_quantity")
# 			}
#
# 			for combination in variation.get("attribute_combinations"):
# 				magento_item_variant["variant_title"] += " | " + combination["value_name"]
#
# 			magento_item.update(magento_item_variant)
#
# 			# Iterate for each attribute assigned to Item
# 			for i, variant_attr in enumerate(template_item_attrib):
# 				if variation.get("attribute_combinations"):
# 					total_magento_combinations = len(variation.get("attribute_combinations"))
#
# 					if i < total_magento_combinations:
# 						attribute_name = variation.get("attribute_combinations")[i]["name"]
# 						attribute_value_name = variation.get("attribute_combinations")[i]["value_name"]
#
# 						attributes[i].update({
# 							"attribute_value": aux_get_attribute_value(attribute_value_name, attribute_name)
# 											})
# 					else:
# 						attributes[i].update({
# 							"attribute_value": "N/A"
# 							})
#
# 			create_item(magento_item, warehouse, 0, attributes, template_item["name"], magento_item_list=magento_item_list)


def is_item_exists(magento_item, magento_item_web, attributes=None, magento_item_list=[]):
	magento_settings = frappe.get_doc("Magento Settings", "Magento Settings")

	colppy_filters = [
        {
            "field": "idItem",
            "op": "<>",
            "value": magento_item.get("codigo")
        }
    ]
	item_exist = get_request("Inventario", "listar_itemsinventario", colppy_filters)

	# by_item_code = frappe.db.get_value(doctype="Item",
	# 								filters={"item_code": magento_item.get("magento_sku")},
	# 								fieldname=["modified", "item_code", "magento_product_id", "magento_variant_id", "variant_of"],
	# 								ignore=1,
	# 								as_dict=True)
	# by_magento_code = frappe.db.get_value(doctype="Item",
	# 								filters={"item_code": magento_item.get("item_code")},
	# 								fieldname=["modified", "item_code", "magento_product_id", "magento_variant_id", "variant_of"],
	# 								ignore=1,
	# 								as_dict=True)

	# item_exist = by_item_code if by_item_code else by_magento_code

	# Tiempo en UTC
	magento_last_updated = datetime.strptime(magento_item.get("updatedAt"), '%Y-%m-%dT%H:%M:%S.%fZ') - timedelta(hours=3)
	last_sync_datetime = datetime.strptime(magento_settings.last_sync_datetime, '%Y-%m-%d %H:%M:%S.%f')

	if item_exist:
		# if "magento_product_id" in item_exist and item_exist.magento_product_id != "No Sync" or\
		# 	"magento_variant_id" in item_exist and item_exist.magento_variant_id != "No Sync":

		if magento_last_updated > last_sync_datetime:
			if magento_last_updated > item_exist.fechaAlta:
				magento_item_list.append(cstr(magento_item.get("codigo")))
				############### LOG ###############
				# make_magento_log(title="Item del Ecommerce modificado", status="Error", method="is_item_exists",
				# message=frappe.get_traceback(), request_data="ERP Item < Last Sync < Meli Item", exception=False)
				###################################
				return False
			else:
				############### LOG ###############
				# make_magento_log(title="Item del ERP modificado, status="Error", method="is_item_exists",
				# message=frappe.get_traceback(), request_data="Last Sync < Meli Item < ERP Item", exception=False)
				###################################
				return True
		else:
			if item_exist.fechaAlta > last_sync_datetime:
				############### LOG ###############
				# make_magento_log(title="Item del ERP modificado", status="Error", method="is_item_exists",
				# message=frappe.get_traceback(), request_data="Meli Item < Last Sync < ERP Item", exception=False)
				###################################
				return True
			else:
				############### LOG ###############
				# make_magento_log(title="Sin modificaciones", status="Error", method="is_item_exists",
				# message=frappe.get_traceback(), request_data="Meli Item < ERP Item < Last Sync", exception=False )
				###################################
				return True

		# else:
		# 	############### LOG ###############
		# 	# make_magento_log(title="Item existente pero no sincronizado", status="Error", method="is_item_exists",
		# 	# message=frappe.get_traceback(), request_data="Item Exist but without Sync", exception=False)
		# 	###################################
		# 	magento_item_list.append(cstr(magento_item.get("magento_product_id")))
		# 	return False

	else:
		magento_item_list.append(cstr(magento_item_web.get("id")))
		############### LOG ###############
		# make_magento_log(title="Item del Ecommerce inexistente en ERP", status="Error", method="is_item_exists",
		# message=frappe.get_traceback(), request_data="Item NO Exist in ERP", exception=False)
		###################################
		return False


def get_item_details(magento_item):
	item_details = {}
	colppy_filters = [
        {
            "field": "idItem",
            "op": "<>",
            "value": magento_item.get("codigo")
        }
    ]
	item_details = get_request("Inventario", "listar_itemsinventario", colppy_filters)
	# item_details = frappe.db.get_value(doctype="Item",
	# 									filters={"item_code": magento_item.get("item_code")},
	# 									fieldname=["name", "stock_uom", "item_name", "modified"],
	# 									as_dict=1)

	if item_details:
		return item_details
	else:
		return None


def add_to_price_list(magento_item, name):
	# Verifica que no exista el precio
	colppy_filters = [
        {
            "field": "idItem",
            "op": "<>",
            "value": magento_item.get("id")
        }
    ]
	colppy_item = get_request("Inventario", "listar_itemsinventario", colppy_filters)
	# colppy_item = frappe.db.get_value("Item Price", {"item_code": name}, "name")

	if not colppy_item.get("data")[0].get("precioVenta"):
		# doc_item_price = frappe.get_doc({
		# 	"doctype": "Item Price",
		# 	"price_list": frappe.get_doc("Magento Settings", "Magento Settings").price_list,
		# 	"item_code": name,
		# 	"price_list_rate": magento_item.get("price")
		# })
		# doc_item_price.flags.ignore_permissions = True
		# doc_item_price.insert()
		colppy_item["data"][0]["precioVenta"] = magento_item.get("price")
		post_request("Inventario", "editar_iteminventario", colppy_item)

	else:
		# item_rate = frappe.get_doc("Item Price", colppy_item)
		# item_rate.price_list_rate = magento_item.get("price")
		# item_rate.flags.ignore_permissions = True
		# item_rate.save()
		colppy_item["data"][0]["precioVenta"] = magento_item.get("price")
		post_request("Inventario", "editar_iteminventario", colppy_item)


def update_item(item_details, item_dict):
	# (Reemplazar por un GET al ERP)
	# item = frappe.get_doc("Item", item_details.name)
	# item_dict["stock_uom"] = item_details.stock_uom

	# del item_dict["item_code"]
	# del item_dict["variant_of"]

	# item.update(item_dict)
	# item.flags.ignore_mandatory = True
	# item.save()
	post_request("Inventario", "editar_iteminventario", item_dict)



"""/////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////
////////////////////// Conector --> Ecommerce //////////////////////////
////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////"""



def sync_erp_items(price_list, warehouse, magento_item_list):
	magento_settings = frappe.get_doc("Magento Settings", "Magento Settings")

	# Trae la ultima fecha de sincronizacion
	last_sync_condition = ""
	if magento_settings.last_sync_datetime:
		last_sync_condition = "modified >= '{0}' ".format(magento_settings.last_sync_datetime)

	# Trae todos los ITEMS (con sus campos) que se modificaron despues de la ultima sincronizacion
	# Reemplazar por un GET a Colppy/Contabilium
	item_query = """select name, item_code, item_name, item_group, magento_description, description,
		has_variants, stock_uom, image, magento_product_id, magento_variant_id, sync_qty_with_magento,
		magento_sku from tabItem where sync_with_magento=1 and (variant_of is null or variant_of = '')
		and (disabled is null or disabled = 0) and %s """ % last_sync_condition

	make_magento_log(title="Magento list", status="Error", request_data=magento_item_list, exception=False)

	# Itera por cada ITEM del diccionario
	for item in frappe.db.sql(item_query, as_dict=1):
		# Chequea que el ITEM no haya sido creado/modificado en el ERP
		# Chequea que el ITEM no este Finalizado
		# Chequea que el ITEM no sea variante, solo base
		if item.magento_product_id not in magento_item_list:
			try:
				sync_item_with_magento(item, price_list, warehouse)
				frappe.local.form_dict.count_dict["products"] += 1

			except MeliError, e:
				make_magento_log(title=e.message, status="Error", method="sync_binarerp_items", message=frappe.get_traceback(),
					request_data=item, exception=True)
			except Exception, e:
				make_magento_log(title=e.message, status="Error", method="sync_binarerp_items", message=frappe.get_traceback(),
					request_data=item, exception=True)

	sync_erp_prices(last_sync_condition, magento_settings.last_sync_datetime, magento_item_list)


def sync_erp_prices(last_sync_condition, last_sync_datetime, magento_item_list=[]):
	try:
		# Trae todos los PRECIOS que se modificaron despues de la ultima sincronizacion
		# Reemplazar por un GET a Colppy/Contabilium
		item_price_query = """select item_code, price_list_rate from
			`tabItem Price` where %s""" % last_sync_condition

		# Itera por cada PRECIO del diccionario
		for price in frappe.db.sql(item_price_query, as_dict=1):
			# Chequea que el PRECIO no haya sido modificado por el ERP
			if price.item_code not in magento_item_list:
				# Busca el ITEM que corresponda con el PRECIO iterado
				# Reemplazar por un GET a Colppy/Contabilium
				magento_product_id = frappe.db.get_value(doctype="Item",
														filters={"item_code": price.item_code},
														fieldname=["magento_product_id", "magento_variant_id"],
														as_dict=1)

				# Chequea el producto este sincronizado
				# No aplica en Colppy/Contabilium
				# if magento_product_id["magento_variant_id"] != "No Sync":
				# 	for variation in get_request("/items/{0}".format(magento_product_id["magento_product_id"])).get("variations"):
				# 		magento_variation_data = {
				# 			"price": price["price_list_rate"],
				# 			"attribute_combinations": []
				# 		}
				# 		for attr_combination in variation.get("attribute_combinations"):
				#
				# 			magento_variation_data["attribute_combinations"].append(
				# 				{
				# 					"id": attr_combination.get("id"),
				# 					"value_id": attr_combination.get("value_id")
				# 				}
				# 			)
				#
				# 		magento_variation = {
				# 			"variations": [
				# 				magento_variation_data
				# 			]
				# 		}
				# 	put_request("/items/{0}".format(magento_product_id["magento_product_id"]), magento_variation)
				# else:
				put_request("/items/{0}".format(magento_product_id["magento_product_id"]), {"price": price["price_list_rate"]})
	except Exception, e:
		make_magento_log(title=e.message, status="Error", message=frappe.get_traceback(), exception=True)


def sync_item_with_magento(item, price_list, warehouse):
	variant_item_name_list = []

	# Se emparejan las keys del Ecommerce con las del ERP
	item_data = {
		"title": item.get("item_name"),
		"seller_custom_field": item.get("name"),
		"description": item.get("magento_description") or item.get("description"),
		"currency_id": "ARS",
		"shipping": {},
		"text": item.get("magento_description")
	}

		# item_data = {
		# 	"title": item.get("item_name"),
		# 	"seller_custom_field": item.get("name"),
		# 	"category_id": item.get("magento_category_id"),
		# 	"listing_type_id": frappe.db.get_value("Meli Listing Type",
		#										  {"name_listing_type": item.get("listing_type_id")},
		#										  ["id_listing_type"]),
		# 	"description": item.get("magento_description") or item.get("description"),
		# 	"buying_mode": "buy_it_now",
		# 	"condition": "new" if item.get("magento_condition") == "Nuevo" else "used",
		# 	"currency_id": "ARS",
		# 	"video_id": item.get("magento_url_video"),
		# 	"warranty": item.get("magento_warranty"),
		# 	"shipping": {
		# 		"mode": "me2",
		# 		"local_pick_up": item.get("magento_local_pick_up"),
		# 		"free_shipping": item.get("magento_free_shipping")
		# 	},
		# 	"tags": [
		# 		"immediate_payment" if item.get("magento_immediate_payment") else None
		# 	]
		# }

	# La descripcion se agrega aparte ya que si forma parte de item_data
	# Meli da error  porque no se puede hacer un PUT con la descripcion
	# item_description = {
	# 	"text": item.get("magento_description")
	# }

	# No aplica en Colppy/Contabilium
	# Construye la key "variations" para productos variables
	# if item.get("has_variants"):
	# 	variant_list, variant_item_name = get_variant_attributes(item, price_list, warehouse)
	# 	item_data["variations"] = variant_list
	# 	variant_item_name_list.extend(variant_item_name)

	# Es un producto simple sin variaciones
	# else:
	price_and_stock_details = get_price_and_stock_details(item, warehouse, price_list)
	item_data["price"] = price_and_stock_details.get("price")
	item_data["available_quantity"] = price_and_stock_details.get("available_quantity")

	# Trae solo el ITEM base, los variables no se usan
	erp_item = frappe.get_doc("Item", item.get("name"))
	erp_item.flags.ignore_mandatory = True

	if item.get("magento_actual_status") == "Finalizado":
		# id_item_exist_in_magento = get_request("/items/{0}".format(item.get("magento_product_id")))
		# if len(id_item_exist_in_magento.get("sub_status")) > 0 and id_item_exist_in_magento.get("sub_status")[0] == "deleted":
		deleted_item = True
	else:
		deleted_item = False

	# Verifica que el producto no exista en Meli o bien que este finalizado (Para crear uno nuevo)
	# En Colppy/Contabilium reemplazar por una verificacion de fechas
	if item.get("magento_product_id") == "No Sync" or deleted_item:
		create_item_in_magento(item_data, erp_item, variant_item_name_list)

	# De otra manera el producto ya existe y debe ser actualizado
	else:
		# update_item_in_magento(item_data, item_description, erp_item, item)
		update_item_in_magento(item_data, erp_item, item)

	frappe.db.commit()


def create_item_in_magento(item_data, erp_item, variant_item_name_list):
	try:
		# Crea un nuevo producto en Meli (con sus imagenes)
		new_item = post_request("/items", item_data)
		erp_item.magento_product_id = new_item.get("id")
		erp_item.permalink = new_item.get("permalink")
		# No aplica en Colppy/Contabilium
		# sync_item_image(erp_item)
		erp_item.save()

		# No aplica en Colppy/Contabilium
		# if new_item.get("variations"):
		# 	# Asigna cada ID de la variacion de Meli a cada variacion del ERP
		# 	update_variant_item(new_item, variant_item_name_list)

	except requests.exceptions.HTTPError, e:
		if e.args[0] and e.args[0].startswith("404") or e.args[0].startswith("403"):
			disable_magento_sync_for_item(erp_item)
		else:
			raise e


# def update_item_in_magento(item_data, item_description, erp_item, item):
def update_item_in_magento(item_data, erp_item, item):
	try:
		# put_request("/items/{0}/description".format(item.get("magento_product_id")), item_description)

		# del item_data["description"] # La descripcion no es modificable por este medio
		# del item_data["category_id"] # La categoria no es modificable
		# del item_data["listing_type_id"] # El tipo de publicacion no es modificable

		put_request("/items/{0}".format(item.get("magento_product_id")), item_data)
		# No aplica en Colppy/Contabilium
		# sync_item_image(erp_item)

	except requests.exceptions.HTTPError, e:
		if e.args[0] and e.args[0].startswith("404") or e.args[0].startswith("403"):
			disable_magento_sync_for_item(erp_item)
		else:
			raise e

# No aplica en Colppy/Contabilium
# def sync_item_image(item):
#
# 	magento_item = get_request("/items/{0}".format(item.magento_product_id))
#
# 	# Borra todas las imagenes existentes en el item de MercadoLibre
# 	# Reemplazar por un GET a Colppy/Contabilium
# 	for magento_image in magento_item.get("pictures"):
# 		delete_request("/items/{0}/pictures/{1}".format(item.magento_product_id, magento_image.get("id")))
#
# 	# Verifica que exista imagen principal (de otra manera no se activan las otras imagenes)
# 	if item.image:
# 		# img_details = frappe.db.get_all("File", {"attached_to_name": item.name}, ["file_name", "content_hash", "file_url"])
# 		# img_details = frappe.db.get_all("Item", {"attached_to_name": item.name}, ["file_name", "content_hash", "file_url"])
# 		pictures = {
# 			"pictures": []
# 		}
# 		img_details = [
# 						{"file_url": item.image or None},
# 						{"file_url": item.image_1 or None},
# 						{"file_url": item.image_2 or None},
# 						{"file_url": item.image_3 or None},
# 						{"file_url": item.image_4 or None}]
#
# 		if img_details:
# 			for file_image in img_details:
# 				# Verfica que exista la imagen en el item y este en el servidor
# 				if file_image["file_url"] != None and file_image["file_url"].startswith("/"):
# 					is_private = file_image["file_url"].startswith('/private/files')
#
# 					file = {"file": open(get_files_path(file_image["file_url"].strip('/private/files/'), is_private=is_private), "rb")}
# 					put_images(item.magento_product_id, file)
#
# 				# Verifica que no sea https, ya que no es aceptado por MercadoLibre
# 				elif file_image["file_url"] != None\
# 				and file_image["file_url"].startswith("http")\
# 				and not file_image["file_url"].startswith("https")\
# 				or file_image["file_url"].startswith("ftp"):
# 					if validate_image_url(file_image["file_url"]):
#
# 						url_dict = {}
# 						url_dict["url"] = file_image["file_url"]
# 						# url_dict = {
# 						# 	"url": item.image
# 						# }
#
# 						pictures["pictures"].append(url_dict)
# 						# pictures = {
# 						# 	"pictures": [
# 						# 		{ "url": item.image }
# 						# 	]
# 						# }
#
# 						try:
# 							put_request("/items/{0}".format(item.magento_product_id), pictures)
#
# 						except requests.exceptions.HTTPError, e:
# 							if e.args[0] and e.args[0].startswith("404") or e.args[0].startswith("403"):
# 								disable_magento_sync_for_item(item)
# 							else:
# 								raise e
#
# # No aplica en Colppy/Contabilium
# def validate_image_url(url):
# 	# Check on given url image exists or not
# 	res = requests.get(url)
# 	if res.headers.get("content-type") in ('image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff'):
# 		return True
# 	return False

# No aplica en Colppy/Contabilium
# def update_variant_item(new_item, item_code_list):
# 	for i, name in enumerate(item_code_list):
# 		erp_item = frappe.get_doc("Item", name)
# 		erp_item.flags.ignore_mandatory = True
# 		erp_item.magento_product_id = new_item.get("id")
# 		erp_item.magento_variant_id = new_item.get("variations")[i].get("id")
# 		erp_item.magento_permalink = new_item.get("permalink")
# 		erp_item.save()

# No aplica en Colppy/Contabilium
# def get_variant_attributes(item, price_list, warehouse):
# 	variant_list, variant_item_name = [], [], []
#
# 	# Itera sobre todos los ITEMs que sean la variante del BASE en cuestion
# 	for i, variant in enumerate(frappe.get_all(doctype="Item",
# 												filters={"variant_of": item.get("name")},
# 												fields=['name'])):
#
# 		# Se controla si se desea sincronizar esa variante
# 		if variant.sync_with_magento:
# 			item_variant = frappe.get_doc("Item", variant.get("name"))
# 			variant_list.append(get_price_and_stock_details(item_variant, warehouse, price_list))
#
# 			# Itera sobre todos los ATRIBUTOS de la VARIANTE en cuestion
# 			for x, attr in enumerate(item_variant.get('attributes')):
#
# 				if attr.idx <= 3:
# 					variant_list[i]["attribute_combinations"][x]["id"] = attr.attribute
# 					variant_list[i]["attribute_combinations"][x]["name"] = ""
# 					variant_list[i]["attribute_combinations"][x]["value_id"] = attr.attribute_value
# 					variant_list[i]["attribute_combinations"][x]["value_name"] = ""
#
# 			variant_item_name.append(item_variant.name)
#
# 	return variant_list, variant_item_name
# 	# variant_list = [
# 	# 	{
# 	#		"attribute_combinations": [
# 	#			"id": 83000,
# 	#			"name": "Color Primario",
# 	#			"value_id": 67655,
# 	#			"value_name": "Blanco",
# 	#		],
# 	#		[
# 	#			"id": 93000,
# 	#			"name": "Talle",
# 	#			"value_id": 98996,
# 	#			"value_name": "M",
# 	#		],
# 	# 		"id": 120039886 or "No Sync",
# 	# 		"price": 200,
# 	# 		"available_quantity": 5
# 	# 	}
# 	# ]
#
# 	# options = []
#
# 	# variant_item_name = [
# 	# 	"ROPA0001-BLANCO-M", "ROPA0001-BEIGE-S"
# 	# ]


def get_price_and_stock_details(item, warehouse, price_list):
	# Trae las cantidades de la variante
	qty = frappe.db.get_value(doctype="Bin",
								filters={"item_code": item.get("item_code"),
										"warehouse": warehouse},
								filedname="actual_qty")

	# Trae el precio de la variante
	price = frappe.db.get_value(doctype="Item Price",
								filters={"price_list": price_list,
										"item_code": item.get("item_code")},
								fieldname="price_list_rate")

	item_price_and_quantity = {
		"price": flt(price)
	}

	if item.get("sync_qty_with_magento"):
		item_price_and_quantity.update({
			"available_quantity": cint(qty) if qty else 0
		})

	# if item.magento_variant_id:
	# 	item_price_and_quantity["id"] = item.magento_variant_id

	return item_price_and_quantity
	# {
	#	"id": 120039886 or "No Sync"
	# 	"price": 200,
	# 	"available_quantity": 5
	# }


# Se ejecuta cuando se da un cambio de stock
def trigger_update_item_stock(doc, method):
	if doc.flags.via_stock_ledger_entry:
		magento_settings = frappe.get_doc("Magento Settings", "Magento Settings")
		item = frappe.get_doc("Item", doc.item_code)

		# Solo dispara la actualización de stock si:
		# 1- El Item no esta deshabilitado
		# 2- La sincronizacion esta activa
		if is_magento_enabled() and not item.disabled:
			update_item_stock(doc.item_code, magento_settings, doc)


# Se ejecuta desde api.py cada hora
def update_item_stock_qty(magento_item_list):
	magento_settings = frappe.get_doc("Magento Settings")

	# Para cada item que este SINCRONIZADO y NO DESHABILITADO
	for item in frappe.get_all(doctype="Item",
								fields=["item_code"],
								filters={"sync_with_magento": 1,
										"disabled": ("!=", 1)}):
		# ITEM CODE:
		# En el caso de ITEM BASE: es el Meli ID
		# En el caso de ITEM VARIANTE: es el Meli Variant ID
		try:
			update_item_stock(item.item_code, magento_settings)
		except MeliError, e:
			make_magento_log(title=e.message, status="Error", method="sync_magento_items", message=frappe.get_traceback(),
				request_data=item, exception=True)

		except Exception, e:
			if e.args[0] and e.args[0].startswith("402"):
				raise e
			else:
				make_magento_log(title=e.message, status="Error", method="sync_magento_items", message=frappe.get_traceback(),
					request_data=item, exception=True)


def update_item_stock(item_code, magento_settings, bin_doc=None):

	item = frappe.get_doc("Item", item_code)
	if item.sync_qty_with_magento:
		# Si no existe una entrada de inventario, la crea
		if not bin_doc:
			bin_doc = get_bin(item_code, magento_settings.warehouse)

		# Si el item es BASE y no esta SINCRONIZADO (Revisar el Flow)
		if item.magento_product_id == "No Sync" and not item.variant_of:
			sync_item_with_magento(item, magento_settings.price_list, magento_settings.warehouse)

		# Si el item se va a sincronizar, tiene id de de Meli y coincide con el almacen de Meli
		if item.sync_with_magento and item.magento_product_id and magento_settings.warehouse == bin_doc.warehouse:
			resource = "/items/{0}".format(item.magento_product_id)

			# Es un item variante?
			if item.variant_of:
				item_data = {
					"variations": [
						{
							"id": item.magento_variant_id,
							"available_quantity": cint(bin_doc.actual_qty)
						}
					]
				}

			if cint(bin_doc.actual_qty) == 0:
				pass
				# put_request("/items/{0}".format(item.magento_product_id), {"available_quantity": 1, "status": "paused"})
				# item.magento_actual_status = "Pausado"

			# Es un item simple?
			else:
				item_data = {
					"available_quantity": cint(bin_doc.actual_qty)
				}

			try:
				put_request(resource, item_data)
			except requests.exceptions.HTTPError, e:
				if e.args[0] and e.args[0].startswith("404") or e.args[0].startswith("403"):
					disable_magento_sync_for_item(item)
				else:
					raise e


####### AUXILIARES Ecommerce --> ERP #######

# No aplica en Colppy/Contabilium
# def aux_item_dict_images(item_dict, magento_item, variant_of):
# 	if variant_of:
# 		for i, image in enumerate(magento_item.get("pictures")):
# 			if i == 0:
# 				item_dict["image"] = image.get("secure_url")
# 			else:
# 				item_dict["image_" + str(i)] = image.get("secure_url")
# 	else:
# 		for i, image_variation in enumerate(magento_item.get("variations")):
# 			if image_variation.get("id") == item_dict["magento_variant_id"]:
# 				image_url = get_variation_picture(image_variation[i].get("picture_ids"))
# 				if i == 0:
# 					item_dict["image"] = image_url
# 				else:
# 					item_dict["image_" + str(i)] = image_url

# No aplica en Colppy/Contabilium
# def aux_get_attribute_value(variant_attr_val, attribute):
# 	attribute_value = frappe.db.sql("""select attribute_value from `tabItem Attribute Value`
# 		where parent = %s and (abbr = %s or attribute_value = %s)""", (attribute, variant_attr_val,
# 		variant_attr_val), as_list=1)
# 	return attribute_value[0][0] if len(attribute_value) > 0 else cint(variant_attr_val)

# No aplica en Colppy/Contabilium
# def aux_get_category(category_id):
# 	get_category = get_request("/categories/{0}".format(category_id))
# 	category_path = ""
#
# 	for category in get_category.get("path_from_root"):
# 		category_path += " > " + category.get("name")
#
# 	return category_path

# No aplica en Colppy/Contabilium
# def aux_get_status(status, substatus):
# 	if not substatus:
# 		if status == "active":
# 			return "Activo"
# 		elif status == "paused":
# 			return "Pausado"
# 		elif status == "closed":
# 			return "Finalizado"
#
# 	elif substatus and substatus[0] == "deleted" and status == "closed":
# 			return "Eliminado"

# No aplica en Colppy/Contabilium
# def aux_get_item_description(id_item):
# 	description = get_request("items/{0}/description".format(id_item))
#
# 	if description.get("text"):
# 		return description.get("text")
# 	else:
# 		return description.get("plain_text")


####### AUXILIARES ERP --> Ecommerce #######

# No aplica en Colppy/Contabilium
# def predict_category(doc, method):
#
# 	if doc.item_name and not doc.magento_category_id:
# 		prediction = get_prediction_resource("/sites/MLA/category_predictor/predict?title={0}".format(doc.item_name))
# 		category_id = ""
# 		category_path = ""
#
# 		for category in prediction.get("path_from_root"):
# 			category_path += " > " + category.get("name")
# 			category_id = category.get("id")
#
# 		make_magento_log(title="Category Predict On Update", status="Error", method="sync_magento_items", message=frappe.get_traceback(),
# 			request_data=category_path, exception=False)
#
# 		frappe.db.set_value("Item", doc.name, "magento_category_id", category_id)
# 		frappe.db.set_value("Item", doc.name, "magento_category", category_path)
# 		frappe.db.commit()

# No aplica en Colppy/Contabilium
# def get_status_erp(status):
# 	if status == "Activar" or status == "Activo":
# 		return "active"
# 	elif status == "Pausar" or status == "Pausado":
# 		return "paused"
# 	elif status == "Finzalizar" or status == "Finzalido":
# 		return "closed"


def get_weight_in_grams(weight, weight_uom):
	convert_to_gram = {
		"kg": 1000,
		"lb": 453.592,
		"oz": 28.3495,
		"g": 1
	}

	return weight * convert_to_gram[weight_uom.lower()]
