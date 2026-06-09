# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe
from books_integration import __version__ as app_version


@frappe.whitelist(methods=["GET"])
def sync_settings(instance=None):
    return {
        "success": True,
        "app_version": app_version,
        "data": frappe.get_cached_doc("Books Sync Settings").generate_sync_params(instance)
    }


def _get_default_pos_profile():
    return frappe.db.get_value("POS Profile", {"disabled": 0}, "name") or frappe.db.get_value("POS Profile", {}, "name")


def _ensure_item_settings(pos_profile):
    if frappe.db.get_single_value("Books Item Settings", "price_list"):
        return

    price_list = None
    if pos_profile:
        price_list = frappe.db.get_value("POS Profile", pos_profile, "selling_price_list")

    if not price_list:
        price_list = frappe.db.get_value("Price List", {"enabled": 1, "selling": 1}, "name")

    if price_list:
        frappe.db.set_single_value("Books Item Settings", "price_list", price_list)


def _queue_doc_for_instance(instance, doctype, docname):
    if not docname:
        return

    queue_doc = {
        "doctype": "Books Sync Queue",
        "document_type": doctype,
        "document_name": docname,
        "books_instance": instance,
    }
    if not frappe.db.exists(queue_doc):
        frappe.get_doc(queue_doc).insert(ignore_permissions=True)


def _seed_master_data(instance):
    master_doctypes = (
        ("Price List", {"enabled": 1}),
        ("Item", {"disabled": 0}),
        ("Customer", {"disabled": 0}),
        ("Supplier", {"disabled": 0}),
        ("UOM", {}),
        ("Address", {}),
        ("Batch", {"disabled": 0}),
        ("Serial No", {}),
    )

    for doctype, filters in master_doctypes:
        for docname in frappe.get_all(doctype, filters=filters, pluck="name"):
            _queue_doc_for_instance(instance, doctype, docname)


@frappe.whitelist(methods=["POST"])
def register_instance(instance, instance_name=None):
    if not instance:
        return {"success": False, "message": "Instance name is required"}

    pos_profile = _get_default_pos_profile()
    _ensure_item_settings(pos_profile)

    if frappe.db.exists("Books Instance", instance):
        doc = frappe.get_doc("Books Instance", instance)
        changed = False
        if not doc.enabled:
            doc.enabled = 1
            changed = True
        if instance_name and doc.instance_name != instance_name:
            doc.instance_name = instance_name
            changed = True
        elif not doc.instance_name:
            doc.instance_name = instance
            changed = True
        if pos_profile and not doc.pos_profile:
            doc.pos_profile = pos_profile
            changed = True
        if changed:
            doc.save(ignore_permissions=True)
        _seed_master_data(instance)
        return {"success": True, "message": "Instance already registered"}

    frappe.get_doc({
        "doctype": "Books Instance",
        "enabled": 1,
        "device_id": instance,
        "instance_name": instance_name or instance,
        "pos_profile": pos_profile,
    }).insert(ignore_permissions=True)

    _seed_master_data(instance)

    return {"success": True, "message": "Instance registered successfully"}
