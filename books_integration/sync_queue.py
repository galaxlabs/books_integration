# Copyright (c) 2024, Wahni IT Solutions and contributors
# For license information, please see license.txt

import frappe


def add_doc_to_sync_queue(doc, method=None):
    if frappe.flags.in_books_process:
        return

    if doc.meta.is_submittable and doc.docstatus == 0:
        return

    if not document_should_sync(doc.doctype):
        return

    instances = frappe.db.get_all(
        "Books Instance",
        # filters={"enable_sync": 1},
        pluck="name",
    )
    for instance in instances:
        is_exists_in_queue = frappe.db.exists(
            {
                "doctype": "Books Sync Queue",
                "document_name": doc.name,
                "document_type": doc.doctype,
                "books_instance": instance,
            }
        )
        if not is_exists_in_queue:
            frappe.get_doc(
                {
                    "doctype": "Books Sync Queue",
                    "document_name": doc.name,
                    "document_type": doc.doctype,
                    "books_instance": instance,
                }
            ).insert()


def document_should_sync(doctype):
    settings = frappe.get_cached_doc("Books Sync Settings")
    if not settings.enable_sync:
        return False

    if doctype == "Item Price":
        doctype = ["Price List"]
    elif doctype == "Mode of Payment":
        doctype = ["Sales Invoice", "Payment Entry"]
    else:
        doctype = [doctype]

    # for row in settings.sync_docs:
    #     if row.document_type in doctype:
    #         return True
    return True

    # return False

def _queue_doc(instance, doctype, docname):
    if not docname:
        return

    queue_doc = {
        "doctype": "Books Sync Queue",
        "document_name": docname,
        "document_type": doctype,
        "books_instance": instance,
    }
    if not frappe.db.exists(queue_doc):
        frappe.get_doc(queue_doc).insert()


def add_item(doc, method=None):
    # Runs when Item Price is modified. Queue both the item and its parent price list.
    instances = frappe.db.get_all(
        "Books Instance",
        # filters={"enable_sync": 1},
        pluck="name",
    )
    for instance in instances:
        _queue_doc(instance, "Item", doc.item_code)
        _queue_doc(instance, "Price List", doc.price_list)