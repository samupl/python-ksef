"""XML converters used to convert library models into KSEF-compliant XML files."""
from typing import cast
from xml.etree import ElementTree

from ksef.models.invoice import Invoice


def convert_invoice_to_xml(invoice: Invoice) -> bytes:
    """Convert an invoice model instance to XML document representing this invoice."""
    root = ElementTree.Element("Faktura")

    header = ElementTree.SubElement(root, "Naglowek")
    form_code = ElementTree.SubElement(
        header,
        "KodFormularza",
        attrib={"kodSystemowy": "FA (1)", "wersjaSchemy": "1-0E"},
    )
    form_code.text = "FA"
    form_variant = ElementTree.SubElement(header, "WariantFormularza")
    form_variant.text = "1"

    return cast(bytes, ElementTree.tostring(root, encoding="utf-8", xml_declaration=True))
