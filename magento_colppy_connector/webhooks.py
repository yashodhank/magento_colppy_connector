from __future__ import unicode_literals
import frappe
from frappe import _
from functools import wraps
import hashlib, base64, hmac, json
from .utils import make_meli_log
from frappe.exceptions import AuthenticationError, ValidationError
from meli_requests import get_request, post_request, get_meli_items, put_request, put_images, delete_request, get_prediction_resource
from sync_orders import webhook_meli_orders
from sync_products import create_item


@frappe.whitelist(allow_guest=True)
def webhook():
	webhook_data = frappe._dict(json.loads(frappe.local.request.get_data()))
	topic = webhook_data.get("topic")
	resource = get_request(webhook_data.get("resource"))

	make_meli_log(title="Webhook Topic", status="Error", method="webhook", message="",
		request_data=topic, exception=False)

	make_meli_log(title="Webhook", status="Error", method="webhook", message="",
		request_data=resource, exception=False)

	if topic == "items":
		change_status(resource)
	elif topic == "created_orders" or topic == "orders":
		webhook_meli_orders(resource)
	elif topic == "questions":
		pass
	elif topic == "payments":
		pass
	elif topic == "pictures":
		pass

def change_status(meli_item):

	meli_actual_status = frappe.db.get_value(doctype="Item",
											filters={"meli_product_id": meli_item.get("id")},
											fieldname=["meli_actual_status"],
											as_dict=1)
	status = meli_item.get("status")
	meli_id = meli_item.get("id")
	erp_item_name = frappe.db.get_value("Item", {"meli_product_id": meli_id})
	erp_item = frappe.get_doc("Item", erp_item_name)

	if meli_actual_status:
		if status == "active" and meli_actual_status != "active":
			erp_item.meli_actual_status = "Activo"
		elif status == "paused" and meli_actual_status != "paused":
			erp_item.meli_actual_status = "Pausado"
		elif status == "under_review" and meli_actual_status != "paused":
			erp_item.meli_actual_status = "Pausado"
		elif status == "closed" and meli_actual_status != "closed":
			erp_item.meli_actual_status = "Finalizado"
			erp_item.disabled = 1
			erp_item.sync_with_meli = 0
	else:
		pass
		# create_item(meli_item, meli_settings.warehouse, has_variant=0, )

	erp_item.save(ignore_permissions=True)


# def shopify_webhook(f):
# 	"""
# 	A decorator thats checks and validates a Shopify Webhook request.
# 	"""
#
# 	def _hmac_is_valid(body, secret, hmac_to_verify):
# 		secret = str(secret)
# 		hash = hmac.new(secret, body, hashlib.sha256)
# 		hmac_calculated = base64.b64encode(hash.digest())
# 		return hmac_calculated == hmac_to_verify
#
# 	@wraps(f)
# 	def wrapper(*args, **kwargs):
# 		# Try to get required headers and decode the body of the request.
# 		try:
# 			webhook_topic = frappe.local.request.headers.get('X-Shopify-Topic')
# 			webhook_hmac	= frappe.local.request.headers.get('X-Shopify-Hmac-Sha256')
# 			webhook_data	= frappe._dict(json.loads(frappe.local.request.get_data()))
# 		except:
# 			raise ValidationError()
#
# 		# Verify the HMAC.
# 		if not _hmac_is_valid(frappe.local.request.get_data(), get_shopify_settings().password, webhook_hmac):
# 			raise AuthenticationError()
#
# 			# Otherwise, set properties on the request object and return.
# 		frappe.local.request.webhook_topic = webhook_topic
# 		frappe.local.request.webhook_data  = webhook_data
# 		kwargs.pop('cmd')
#
# 		return f(*args, **kwargs)
# 	return wrapper
#
#
# @frappe.whitelist(allow_guest=True)
# @shopify_webhook
# def webhook_handler():
# 	from webhooks import handler_map
# 	topic = frappe.local.request.webhook_topic
# 	data = frappe.local.request.webhook_data
# 	handler = handler_map.get(topic)
# 	if handler:
# 		handler(data)
#
# def create_webhooks():
# 	settings = get_shopify_settings()
# 	for event in ["orders/create", "orders/delete", "orders/updated", "orders/paid", "orders/cancelled", "orders/fulfilled",
# 		"orders/partially_fulfilled", "order_transactions/create", "carts/create", "carts/update",
# 		"checkouts/create", "checkouts/update", "checkouts/delete", "refunds/create", "products/create",
# 		"products/update", "products/delete", "collections/create", "collections/update", "collections/delete",
# 		"customer_groups/create", "customer_groups/update", "customer_groups/delete", "customers/create",
# 		"customers/enable", "customers/disable", "customers/update", "customers/delete", "fulfillments/create",
# 		"fulfillments/update", "shop/update", "disputes/create", "disputes/update", "app/uninstalled",
# 		"channels/delete", "product_publications/create", "product_publications/update",
# 		"product_publications/delete", "collection_publications/create", "collection_publications/update",
# 		"collection_publications/delete", "variants/in_stock", "variants/out_of_stock"]:
#
# 		create_webhook(event, settings.webhook_address)
#
# def create_webhook(topic, address):
# 	post_request('admin/webhooks.json', json.dumps({
# 		"webhook": {
# 			"topic": topic,
# 			"address": address,
# 			"format": "json"
# 		}
# 	}))
#
# def get_webhooks():
# 	webhooks = get_request("/admin/webhooks.json")
# 	return webhooks["webhooks"]
#
# def delete_webhooks():
# 	webhooks = get_webhooks()
# 	for webhook in webhooks:
# 		delete_request("/admin/webhooks/{}.json".format(webhook['id']))
