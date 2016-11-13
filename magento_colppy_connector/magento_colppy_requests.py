from __future__ import unicode_literals
import frappe
from frappe import _
import json, math, time
from .exceptions import MeliError
from meli_sdk.meli import Meli
from .utils import make_meli_log
import base64, requests
import requests
import hashlib
import magento_sdk


# def meli_dict():
# 	return frappe.get_doc("Meli Settings")
#
#
# def meli_instance(**kwargs):
# 	meli = Meli(client_id=6494221773772380, client_secret="nVurdurdZhMygSBjV898MOiiBePRRXzs", access_token=kwargs.get("access_token"), refresh_token=kwargs.get("refresh_token"))
# 	return meli
#
#
# @frappe.whitelist(allow_guest=True)
# def redirect_access_token():
# 	meli = meli_instance()
# 	redirectUrl = meli.auth_url(redirect_URI="https://" + frappe.utils.get_host_name() + ("/api/method/meli_connector.meli_requests.generate_token"))
# 	frappe.response["type"] = 'redirect'
# 	frappe.response["location"] = redirectUrl
#
#
# @frappe.whitelist(allow_guest=True)
# def generate_token(code):
# 	meli = meli_instance()
# 	access_token = meli.authorize(code=code, redirect_URI="https://" + frappe.utils.get_host_name() + ("/api/method/meli_connector.meli_requests.generate_token"))
# 	refresh_token = meli.refresh_token
#
# 	frappe.db.set_value("Meli Settings", None, "access_token", access_token)
# 	frappe.db.commit()
#
# 	setup_request = get_request("/users/me")
# 	#return setup_request
#
# 	if setup_request.get('status') == 403:
# 		 meli.authorize(code=code, redirect_URI="https://" + frappe.utils.get_host_name() + ("/api/method/meli_connector.meli_requests.generate_token"))
#
# 	else:
# 		frappe.db.set_value("Meli Settings", None, "refresh_token", refresh_token)
# 		frappe.db.set_value("Meli Settings", None, "nickname_meli", setup_request.get("nickname"))
# 		frappe.db.set_value("Meli Settings", None, "id_meli", setup_request.get("id"))
# 		frappe.db.commit()
#
# 		frappe.response["type"] = 'redirect'
# 		frappe.response["location"] = frappe.utils.get_url("/desk#Form/Meli Settings")
#
#
# def is_token_expired():
# 	dict_settings = meli_dict()
# 	meli = meli_instance(access_token=dict_settings.access_token, refresh_token=dict_settings.refresh_token)
#
# 	meli.get_refresh_token()
# 	frappe.db.set_value("Meli Settings", None, "access_token", meli.access_token)
# 	frappe.db.set_value("Meli Settings", None, "refresh_token", meli.refresh_token)
# 	frappe.db.commit()
#
# 	return
#
#
# @frappe.whitelist(allow_guest=True)
# def get_request(path):
# 	dict_settings = meli_dict()
# 	meli = meli_instance()
# 	params = {'access_token' : dict_settings.access_token}
# 	r = meli.get(path=path, params=params)
#
# 	if r.json().get('status') == 401 or r.json().get('status') == 403:
# 		is_token_expired()
#
# 		refresh_dict_settings = meli_dict()
# 		params = {'access_token' : refresh_dict_settings.access_token}
# 		r = meli.get(path=path, params=params)
# 		return r.json()
#
# 	r.raise_for_status()
# 	return r.json()
#
#
# def post_request(path, body=None):
# 	dict_settings = meli_dict()
# 	meli = meli_instance()
# 	params = {'access_token' : dict_settings.access_token}
# 	make_meli_log(title="POST Requests", status="Error", method="post_requests", message=frappe.get_traceback(),
# 		request_data=body, exception=False)
# 	r = meli.post(path=path, body=body, params=params)
#
# 	if r.json().get('status') == 401 or r.json().get('status') == 403:
# 		is_token_expired()
#
# 		refresh_dict_settings = meli_dict()
# 		params = {'access_token' : refresh_dict_settings.access_token}
# 		r = meli.post(path=path, body=body, params=params)
# 		return r.json()
#
# 	r.raise_for_status()
# 	return r.json()
#
#
# def put_request(path, body=None):
# 	dict_settings = meli_dict()
# 	meli = meli_instance()
# 	params = {'access_token' : dict_settings.access_token}
# 	make_meli_log(title="PUT Requests", status="Error", method="put_requests", message=frappe.get_traceback(),
# 		request_data=body, exception=False)
# 	r = meli.put(path=path, body=body, params=params)
#
# 	if r.json().get('status') == 401 or r.json().get('status') == 403:
# 		is_token_expired()
#
# 		refresh_dict_settings = meli_dict()
# 		params = {'access_token' : refresh_dict_settings.access_token}
# 		r = meli.put(path=path, body=body, params=params)
# 		return r.json()
#
# 	r.raise_for_status()
# 	return r.json()
#
#
# def delete_request(path):
# 	dict_settings = meli_dict()
# 	meli = meli_instance()
# 	params = {'access_token' : dict_settings.access_token}
# 	r = meli.delete(path=path, params=params)
#
# 	if r.json().get('status') == 401 or r.json().get('status') == 403:
# 		is_token_expired()
#
# 		refresh_dict_settings = meli_dict()
# 		params = {'access_token' : refresh_dict_settings.access_token}
# 		r = meli.delete(path=path, params=params)
# 		return r.json()
#
# 	r.raise_for_status()
# 	return r.json()
#
#
# def get_prediction_resource(path, params=None):
# 	meli = meli_instance()
# 	r = meli.get(path=path, params=params)
# 	r.raise_for_status()
# 	return r.json()
#
#
# def put_images(item, files):
# 	dict_settings = meli_dict()
# 	meli = meli_instance()
#
# 	r = requests.post("https://api.mercadolibre.com/pictures?access_token={0}".format(dict_settings.access_token),
# 						files=files)
#
# 	# make_meli_log(title="PUT Images to ML Server", status="Error", method="put_images", message=frappe.get_traceback(),
# 	# 	request_data=r.json() , exception=False)
#
# 	id_image = {
# 		"id": r.json().get("id")
# 	}
#
# 	s = meli.post("https://api.mercadolibre.com/items/{0}/pictures?access_token={1}".format(item, dict_settings.access_token),
# 				body=id_image)
#
# 	# make_meli_log(title="PUT Images to ML Item", status="Error", method="put_images", message=frappe.get_traceback(),
# 	# 	request_data=s.json() , exception=False)
#
# 	return s.json()
#
#
# def get_attributes(category):
# 	r = requests.get("https://api.mercadolibre.com/categories/{0}/attributes".format(category))
# 	return r.json()
#
#
# def get_total_pages_items(ignore_filter_conditions=False):
# 	dict_settings = meli_dict()
#
# 	paging_items = get_request('/users/{0}/items/search'.format(dict_settings.id_meli)).get('paging')
# 	total_items = paging_items.get('total')
# 	total_pages = int(math.ceil(total_items / 50))
#
# 	if total_pages == 0:
# 		return 1, total_items
# 	else:
# 		return total_pages, total_items
#
# 	return paging_items
#
#
# def get_total_pages_orders(ignore_filter_conditions=False):
# 	dict_settings = meli_dict()
#
# 	paging_orders = get_request('/orders/search/pending?seller={0}'.format(dict_settings.id_meli)).get('paging')
# 	total_orders = paging_orders.get('total')
# 	total_pages = int(math.ceil(total_orders / 50))
#
# 	if total_pages == 0:
# 		return 1, total_orders
# 	else:
# 		return total_pages, total_orders
#
# 	return paging_orders
#
#
# # def get_country():
# # 	countries = get_request('/countries')
#
# 	#for country in countries:
# 		# Que funcion lo usa?
#
#
# def get_meli_items():
# 	dict_settings = meli_dict()
# 	total_pages, total_items = get_total_pages_items()
# 	meli_ids = []
# 	meli_products = []
#
# 	for page_idx in range(0, total_pages):
# 		meli_ids.extend(get_request('/users/{0}/items/search?limit=50&offset={1}'.format(dict_settings.id_meli,
# 			page_idx))['results'])
#
# 		for item in meli_ids:
# 			meli_products.append(get_request('/items/{0}'.format(item)))
#
# 	return meli_products
#
#
# def get_meli_orders(ignore_filter_conditions=False):
# 	dict_settings = meli_dict()
# 	total_pages, total_orders = get_total_pages_orders()
# 	meli_orders = []
#
# 	for page_idx in range(0, total_pages):
# 		meli_orders.extend(get_request('/orders/search/pending?seller={0}&limit=50&offset={1}'.format(dict_settings.id_meli,
# 			page_idx))['results'])
#
# 	return meli_orders
#
#
# def get_meli_item_image(meli_product_id):
# 	pictures = get_request("/items/{0}".format(meli_product_id))
# 	return pictures.get("pictures")
#
#
# def get_variation_picture(picture_id):
#     picture = get_request("/picture/picture_id")
#     return picture.get("variations")[0].get("secure_url")


# def get_meli_customers(ignore_filter_conditions=False):
# 	meli_customers = []
#
# 	for page_idx in xrange(0, get_total_pages("customers", ignore_filter_conditions) or 1):
# 		shopify_customers.extend(get_request('/admin/customers.json?limit=250&page={0}&{1}'.format(page_idx+1,
# 			filter_condition))['customers'])
# 	return shopify_customers

"""
////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////
/////////////////////// Colppy Requests ////////////////////////////
////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////
"""


def connection_data():
	url = "https://login.colppy.com/lib/frontera2/service.php" # Production URL
	# dev_url = "http://staging.colppy.com/lib/frontera2/service.php" # Development URL
	colppy_magento_settings = frappe.get_doc("Colppy Magento Settings")
	md5_dev_user_pass = hashlib.md5(colppy_magento_settings.dev_user_pass).hexdigest()
	md5_user_pass = hashlib.md5(colppy_magento_settings.user_pass).hexdigest()

	params = {
	  "auth": {
	        "usuario": colppy_magento_settings.dev_user,
	        "password": md5_dev_user_pass
	  },
	  "service": {
	        "provision": "",
	        "operacion": ""
	  },
	  "parameters": {
	      "usuario": colppy_magento_settings.user,
	      "password": md5_user_pass
	  }
	}

	filter_dict = {
		"start": 0,
			"limit": None,
			"filter": filter,
			"order": {
				"field": [
					"IdEmpresa"
				],
				"order": "asc"
			}
		}
	# "filter": [
	#     {
	#         "field": "IdEmpresa",
	#         "op": "<>",
	#         "value": "1"
	#     }
	# ]

	return url, params, filter_dict


def colppy_login():
	url, params, filter_dict = connection_data()

	params["service"]["provision"] = "Usuario"
	params["service"]["operacion"] = "iniciar_sesion"

	r = requests.post(url, params)
	clave_sesion = r.json().get("response").get("data").get("claveSesion")

	frappe.db.set_value("Colppy Magento Settings", None, "clave_sesion", clave_sesion)
	frappe.db.commit()


def get_request(provision, operation, filter=[]):
	colppy_login()
	url, params, filter_dict = connection_data()

	params["service"]["provision"] = provision
	params["service"]["operacion"] = operation
	params["parameters"].update(filter_dict)

	r = requests.post(url, params)
	# Devuelve una lista de diccionarios con los resultados
	return r.json().get("response").get("data")


def post_request(provision, operation, data=None):
	colppy_login()
	url, params = connection_data()

	params["service"]["provision"] = provision
	params["service"]["operacion"] = operation
	params.update(data)

	requests.post(url, params)


"""
////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////
/////////////////////// Magento Requests ///////////////////////////
////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////
"""


def magento_login():
	url = 'http://binar.com.ar/magento'
	apiuser = 'njuu1v13jsi6tmw9b08h56bfu7bneblx'
	apipass = '8v3igbdnrxdvfo42a5e4n132c7x8den6'

	client = magento_sdk.API(url, apiuser, apipass)
	return client


@frappe.whitelist(allow_guest=True)
def get_magento_products():
	client = magento_login()

	# order_filter = {'created_at':{'from':'2011-09-15 00:00:00'}}
	products = client.product.list()

	return products
