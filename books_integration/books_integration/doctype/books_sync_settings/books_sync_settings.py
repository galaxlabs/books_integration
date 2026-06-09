# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BooksSyncSettings(Document):
	def generate_sync_params(self, instance=None):
		data = self.as_dict()

		sync_params = {
			"Item": ["sync_item", "item_sync_type"],
			"Customer": ["sync_customer", "customer_sync_type"],
			"Supplier": ["sync_supplier", "supplier_sync_type"],
			"Sales Invoice": ["sync_sales_invoice", "sales_invoice_sync_type"],
			"Payment Entry": ["sync_payment_entry", "payment_entry_sync_type"],
			"Stock Entry": ["sync_stock_entry", "stock_sync_type"],
			"Price List": ["sync_price_list", "price_list_sync_type"],
			"Serial No": ["sync_serial_number", "serial_number_sync_type"],
			"Batch": ["sync_batches", "batch_sync_type"],
			"Delivery Note": ["sync_delivery_note", "delivery_note_sync_type"],
		}

		for (sync, sync_type) in sync_params.values():
			data[sync] = 0
			data[sync_type] = "Two Way"

		sync_docs = getattr(self, "sync_docs", None)
		if sync_docs is None:
			for sync_key in (
				"sync_item",
				"sync_customer",
				"sync_supplier",
				"sync_price_list",
				"sync_serial_number",
				"sync_batches",
			):
				data[sync_key] = 1
			data["server_settings"] = self.get_server_settings(instance)
			return data

		for row in sync_docs:
			param = sync_params.get(row.document_type)
			if not param:
				continue

			data[param[0]] = 1
			data[param[1]] = row.sync_type

		data["server_settings"] = self.get_server_settings(instance)
		return data

	def get_server_settings(self, instance=None):
		pos_profile = None
		if instance:
			pos_profile = frappe.db.get_value("Books Instance", instance, "pos_profile")

		if not pos_profile:
			pos_profile = frappe.db.get_value("POS Profile", {"disabled": 0}, "name")

		settings = {
			"books_instance": instance,
			"books_item_price_list": frappe.db.get_single_value("Books Item Settings", "price_list"),
			"pos_profile": pos_profile,
			"pos_profiles": [],
		}

		profile_names = frappe.get_all("POS Profile", filters={"disabled": 0}, pluck="name")
		for profile_name in profile_names:
			profile = frappe.get_doc("POS Profile", profile_name)
			settings["pos_profiles"].append({
				"name": profile.name,
				"company": profile.company,
				"customer": profile.customer,
				"warehouse": profile.warehouse,
				"selling_price_list": profile.selling_price_list,
				"currency": profile.currency,
				"payments": [row.mode_of_payment for row in profile.get("payments", [])],
				"item_groups": [row.item_group for row in profile.get("item_groups", [])],
				"customer_groups": [row.customer_group for row in profile.get("customer_groups", [])],
			})

		return settings
