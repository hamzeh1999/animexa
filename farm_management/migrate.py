import logging

import click
import frappe

APP_NAME = "farm_management"

logger = frappe.logger("farm_management")
logger.setLevel(logging.INFO)


def after_migrate() -> None:
	"""Keep Module Def records in sync with modules.txt on every migrate.

	Additive only: modules newly declared in modules.txt are created here.
	Modules removed from modules.txt are never auto-deleted - deleting a
	Module Def can cascade (ModuleDef.on_trash removes the module's folder
	from disk under developer_mode) and may orphan any DocType/Workspace/
	Report/etc. still linked to it. Stale entries are only reported so a
	human can remove them deliberately through the Module Def list.
	"""
	declared_modules = set(frappe.get_module_list(APP_NAME))
	existing_modules = set(frappe.get_all("Module Def", filters={"app_name": APP_NAME}, pluck="name"))

	for module_name in sorted(declared_modules - existing_modules):
		_create_module_def(module_name)

	stale_modules = existing_modules - declared_modules
	if stale_modules:
		_report_stale_modules(stale_modules)


def _create_module_def(module_name: str) -> None:
	frappe.get_doc({"doctype": "Module Def", "app_name": APP_NAME, "module_name": module_name}).insert(
		ignore_permissions=True, ignore_if_duplicate=True
	)
	message = f"Added Module Def '{module_name}'"
	logger.info(message)
	click.secho(message, fg="green")


def _report_stale_modules(stale_modules: set[str]) -> None:
	linked_fields = _get_module_linked_fields()

	for module_name in sorted(stale_modules):
		referenced, doctype = _module_is_referenced(module_name, linked_fields)
		if referenced:
			message = f"'{module_name}' removed from modules.txt but still referenced by '{doctype}' - not deleting"
		else:
			message = f"'{module_name}' removed from modules.txt and has no references - safe to delete manually"
		logger.warning(message)
		click.secho(message, fg="yellow")


def _get_module_linked_fields() -> list[tuple[str, str]]:
	"""All (doctype, fieldname) pairs where a Link field points to Module Def."""
	standard = frappe.get_all(
		"DocField",
		filters={"fieldtype": "Link", "options": "Module Def"},
		fields=["parent as doctype", "fieldname"],
	)
	custom = frappe.get_all(
		"Custom Field",
		filters={"fieldtype": "Link", "options": "Module Def"},
		fields=["dt as doctype", "fieldname"],
	)
	return [(d.doctype, d.fieldname) for d in standard + custom if frappe.db.exists("DocType", d.doctype)]


def _module_is_referenced(
	module_name: str, linked_fields: list[tuple[str, str]]
) -> tuple[bool, str | None]:
	for doctype, fieldname in linked_fields:
		if frappe.db.exists(doctype, {fieldname: module_name}):
			return True, doctype
	return False, None
