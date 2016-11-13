# /// sync_products.py ///

# def get_product_update_dict_and_resource_variant(meli_product_id, meli_variant_id):
# 	"""
# 	JSON required to update product
#
# 	item_data =	{
# 		"product": {
# 			"id": 3649706435 (shopify_product_id),
# 			"variants": [
# 				{
# 					"id": 10577917379 (shopify_variant_id),
# 					"inventory_management": "shopify",
# 					"inventory_quantity": 10
# 				}
# 			]
# 		}
# 	}
# 	"""
#
# 	item_data = {
# 		"variations": []
# 	}
#
# 	item_data["id"] = meli_product_id
# 	item_data["variations"].append({
# 		"id": meli_variant_id
# 	})
#
# 	resource = "/items/{}".format(meli_product_id)
# 	return item_data, resource


# def get_sku(item):
# 	if item.get("variants"):
# 		return item.get("variants")[0].get("sku")
# 	return ""


# def get_item_group(product_type=None):
# 	parent_item_group = frappe.utils.nestedset.get_root_of("Item Group")
#
# 	if product_type:
# 		if not frappe.db.get_value("Item Group", product_type, "name"):
# 			item_group = frappe.get_doc({
# 				"doctype": "Item Group",
# 				"item_group_name": product_type,
# 				"parent_item_group": parent_item_group,
# 				"is_group": "No"
# 			}).insert()
# 			return item_group.name
# 		else:
# 			return product_type
# 	else:
# 		return parent_item_group


# def get_supplier(shopify_item):
# 	if shopify_item.get("vendor"):
# 		if not frappe.db.get_value("Supplier", {"shopify_supplier_id": shopify_item.get("vendor").lower()}, "name"):
# 			supplier = frappe.get_doc({
# 				"doctype": "Supplier",
# 				"supplier_name": shopify_item.get("vendor"),
# 				"shopify_supplier_id": shopify_item.get("vendor"),
# 				"supplier_type": get_supplier_type()
# 			}).insert()
# 			return supplier.name
# 		else:
# 			return shopify_item.get("vendor")
# 	else:
# 		return ""
#
# def get_supplier_type():
# 	supplier_type = frappe.db.get_value("Supplier Type", _("Shopify Supplier"))
# 	if not supplier_type:
# 		supplier_type = frappe.get_doc({
# 			"doctype": "Supplier Type",
# 			"supplier_type": _("Shopify Supplier")
# 		}).insert()
# 		return supplier_type.name
# 	return supplier_type

# elif attributes and attributes[0].get("attribute_value"):
# 	variant_of = frappe.db.get_value("Item", {"meli_variant_id": meli_item.meli_variant_id}, "variant_of")
#
# 	# create conditions for all item attributes,
# 	# as we are putting condition basis on OR it will fetch all items matching either of conditions
# 	# thus comparing matching conditions with len(attributes)
# 	# which will give exact matching variant item.
#
# 	conditions = ["(iv.attribute='{0}' and iv.attribute_value = '{1}')"\
# 		.format(attr.get("attribute"), attr.get("attribute_value")) for attr in attributes]
#
# 	conditions = "( {0} ) and iv.parent = it.name ) = {1}".format(" or ".join(conditions), len(attributes))
#
# 	parent = frappe.db.sql(""" select * from tabItem it where
# 		( select count(*) from `tabItem Variant Attribute` iv
# 			where {conditions} and it.variant_of = %s """.format(conditions=conditions) ,
# 		variant_of, as_list=1)
#
# 	if parent:
# 		variant = frappe.get_doc("Item", parent[0][0])
# 		variant.flags.ignore_mandatory = True
#
# 		variant.meli_product_id = meli_item.get("meli_product_id")
# 		variant.meli_variant_id = meli_item.get("meli_variant_id")
# 		variant.save()
#
# 	meli_item_list.append(cstr(meli_item.get("meli_product_id")))
# 	return False

#add_item_weight(meli_item)
#def add_item_weight(meli_item):
#	meli_item["weight"] = shopify_item['variants'][0]["weight"]
#	meli_item["weight_unit"] = shopify_item['variants'][0]["weight_unit"]

# else:
# 	# En MercadoLibre no existen los valores numericos, son todos strings
# 	attribute.append({
# 		"attribute": attr.get("name"),
# 		"from_range": item_attr.get("from_range"),
# 		"to_range": item_attr.get("to_range"),
# 		"increment": item_attr.get("increment"),
# 		"numeric_values": item_attr.get("numeric_values")
# 	})

# def get_item_image(meli_item, id_item_image):
# 	if meli_item.get("pictures"):
# 		for i, image in enumerate(meli_item.get("pictures")):
# 			img_attch = frappe.get_doc({
# 				"doctype": "File",
# 			    "attached_to_name": id_item_image,
# 			    "file_name": meli_item.get('title') + "_img#" + str(i),
# 			    "attached_to_doctype": "Item",
# 			    "is_private": 1,
# 			    "file_url": meli_item.get("pictures")[i].get("url")
# 			})
# 			img_attch.insert()

# def get_price_and_stock_details(item, warehouse, price_list):
# if item.net_weight:
# 	if item.weight_uom and item.weight_uom.lower() in ["kg", "g", "oz", "lb"]:
# 		item_price_and_quantity.update({
# 			"weight_unit": item.weight_uom.lower(),
# 			"weight": item.net_weight,
# 			"grams": get_weight_in_grams(item.net_weight, item.weight_uom)
# 		})

# def get_variant_attributes(item, price_list, warehouse):
# attr_dict = {}
# if not attr_dict.get(attr.attribute):
# 	attr_dict.setdefault(attr.attribute, [])
#
# attr_dict[attr.attribute].append(attr.attribute_value)
# # attr_dict = {
# #	"Color Primario":[
# #						"Blanco",
# #						"Beige"
# # 					],
# #	"Talle":[
# #				"M",
# #				"S"
# # 	]
# # }
# for i, attr in enumerate(attr_dict):
# 	options.append({
# 		"name": attr,
# 		"position": i+1,
# 		"values": list(set(attr_dict[attr]))
# 	})

# def item_image_exists(meli_product_id, image_info, private):
# 	"""check same image exist or not"""
# 	for image in get_meli_item_image(meli_product_id):
# 		if image_info and private:
# 			if image.get("url") == image_info:
# 				return True
# 		elif image_info and private:
# 			if os.path.splitext(image.get("url"))[0].split("/")[-1] == os.path.splitext(image_info.get("source"))[0].split("/")[-1]:
# 				return True
# 		else:
# 			return False

# to avoid image duplication
# if not item_image_exists(item.meli_product_id, source_dict["source"], True):
# 	make_meli_log(title="Pictures Error Duplicate", status="Error", method="sync_item_image", message="",
# 		request_data=pictures, exception=False)
# 	return False

# to avoid 422 : Unprocessable Entity
# if len(pictures["pictures"]) == 0:
# 	return False

# #to avoid 422 : Unprocessable Entity
# if not item_image_exists(item.meli_product_id, pictures["pictures"][i], False):
# 	return False
