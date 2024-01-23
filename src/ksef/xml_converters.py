"""XML converters used to convert library models into KSEF-compliant XML files."""
from typing import cast
from xml.etree import ElementTree

from ksef.models.invoice import Invoice


def convert_invoice_to_xml(invoice: Invoice, invoicing_software_name: str = "python-ksef") -> bytes:
    """Convert an invoice model instance to XML document representing this invoice."""
    root = ElementTree.Element(
        "Faktura",
        attrib={
            "xmlns": "http://ksef.mf.gov.pl/wzor/2021/08/05/08051/",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:tns": "http://ksef.mf.gov.pl/wzor/2021/08/05/08051/",
            "xsi:schemaLocation": "http://crd.gov.pl/wzor/2021/11/29/11089/schemat.xsd",
        },
    )

    # region header
    header = ElementTree.SubElement(root, "Naglowek")
    form_code = ElementTree.SubElement(
        header,
        "KodFormularza",
        attrib={"kodSystemowy": "FA (1)", "wersjaSchemy": "1-0E"},
    )
    form_variant = ElementTree.SubElement(header, "WariantFormularza")
    system_info = ElementTree.SubElement(header, "SystemInfo")

    form_code.text = "FA"
    form_variant.text = "1"
    system_info.text = invoicing_software_name
    # endregion

    # region issuer
    issuer = ElementTree.SubElement(root, "Podmiot1")

    issuer_id_data = ElementTree.SubElement(issuer, "DaneIdentyfikacyjne")
    issuer_nip = ElementTree.SubElement(issuer_id_data, "NIP")
    issuer_nip.text = invoice.issuer.identification_data.nip
    issuer_full_name = ElementTree.SubElement(issuer_id_data, "PelnaNazwa")
    issuer_full_name.text = invoice.issuer.identification_data.full_name

    issuer_address = ElementTree.SubElement(
        issuer, "Adres", attrib={"xsi:type": "tns:TAdresPolski"}
    )
    issuer_country_code = ElementTree.SubElement(issuer_address, "KodKraju")
    issuer_city = ElementTree.SubElement(issuer_address, "Miejscowosc")
    issuer_street = ElementTree.SubElement(issuer_address, "Ulica")
    issuer_house_number = ElementTree.SubElement(issuer_address, "NrDomu")
    issuer_apartment_number = ElementTree.SubElement(issuer_address, "NrLokalu")
    issuer_postal_code = ElementTree.SubElement(issuer_address, "KodPocztowy")

    issuer_country_code.text = invoice.issuer.address.country_code
    issuer_city.text = invoice.issuer.address.city
    issuer_street.text = invoice.issuer.address.street
    issuer_house_number.text = invoice.issuer.address.house_number
    issuer_apartment_number.text = invoice.issuer.address.apartment_number
    issuer_postal_code.text = invoice.issuer.address.postal_code
    # endregion

    # region receiver
    receiver = ElementTree.SubElement(root, "Podmiot2")
    receiver_id_data = ElementTree.SubElement(receiver, "DaneIdentyfikacyjne")
    receiver_nip = ElementTree.SubElement(receiver_id_data, "NIP")
    receiver_nip.text = invoice.recipient.identification_data.nip
    # endregion

    return cast(bytes, ElementTree.tostring(root, encoding="utf-8", xml_declaration=True))
