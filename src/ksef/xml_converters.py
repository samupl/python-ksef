"""XML converters used to convert library models into KSEF-compliant XML files."""
from typing import cast
from xml.etree import ElementTree

from ksef.models.invoice import Invoice


def _build_header(root: ElementTree.Element, invoicing_software_name: str) -> None:
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


def _build_issuer(root: ElementTree.Element, invoice: Invoice) -> None:
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


def _build_receiver(root: ElementTree.Element, invoice: Invoice) -> None:
    receiver = ElementTree.SubElement(root, "Podmiot2")
    receiver_id_data = ElementTree.SubElement(receiver, "DaneIdentyfikacyjne")
    receiver_nip = ElementTree.SubElement(receiver_id_data, "NIP")
    receiver_nip.text = invoice.recipient.identification_data.nip


def _build_invoice_data_annotations(invoice_data: ElementTree.Element, invoice: Invoice) -> None:
    invoice_data_annotations = ElementTree.SubElement(invoice_data, "Adnotacje")
    invoice_data_annotations_tax_settlement_on_payment = ElementTree.SubElement(
        invoice_data_annotations, "P_16"
    )
    invoice_data_annotations_self_invoice = ElementTree.SubElement(invoice_data_annotations, "P_17")
    invoice_data_annotations_reverse_charge = ElementTree.SubElement(
        invoice_data_annotations, "P_18"
    )
    invoice_data_annotations_split_payment = ElementTree.SubElement(
        invoice_data_annotations, "P_18A"
    )
    invoice_data_annotations_free_from_vat = ElementTree.SubElement(
        invoice_data_annotations, "P_19"
    )
    invoice_data_annotations_intra_community_supply_of_new_transport_methods = (
        ElementTree.SubElement(invoice_data_annotations, "P_22")
    )
    invoice_data_annotations_simplified_procedure_by_second_tax_payer = ElementTree.SubElement(
        invoice_data_annotations, "P_23"
    )
    invoice_data_annotations_margin_procedure = ElementTree.SubElement(
        invoice_data_annotations, "P_PMarzy"
    )

    data = invoice.invoice_data
    invoice_data_annotations_tax_settlement_on_payment.text = (
        data.invoice_annotations.tax_settlement_on_payment.value
    )
    invoice_data_annotations_self_invoice.text = data.invoice_annotations.self_invoice.value
    invoice_data_annotations_reverse_charge.text = data.invoice_annotations.reverse_charge.value
    invoice_data_annotations_split_payment.text = data.invoice_annotations.split_payment.value
    invoice_data_annotations_free_from_vat.text = data.invoice_annotations.free_from_vat.value
    ics_value = data.invoice_annotations.intra_community_supply_of_new_transport_methods.value
    invoice_data_annotations_intra_community_supply_of_new_transport_methods.text = ics_value
    sp_value = data.invoice_annotations.simplified_procedure_by_second_tax_payer.value
    invoice_data_annotations_simplified_procedure_by_second_tax_payer.text = sp_value
    invoice_data_annotations_margin_procedure.text = data.invoice_annotations.margin_procedure.value


def _build_invoice_data(root: ElementTree.Element, invoice: Invoice) -> None:
    invoice_data = ElementTree.SubElement(root, "Fa")
    invoice_data_currency_code = ElementTree.SubElement(invoice_data, "KodWaluty")
    invoice_data_issue_date = ElementTree.SubElement(invoice_data, "P_1")
    invoice_data_invoice_number = ElementTree.SubElement(invoice_data, "P_2")
    invoice_data_sell_date = ElementTree.SubElement(invoice_data, "P_6")
    invoice_data_total_amount = ElementTree.SubElement(invoice_data, "P_15")

    invoice_data_currency_code.text = invoice.invoice_data.currency_code
    invoice_data_issue_date.text = invoice.invoice_data.issue_date.strftime("%Y-%m-%d")
    invoice_data_invoice_number.text = invoice.invoice_data.issue_number
    invoice_data_sell_date.text = invoice.invoice_data.sell_date.strftime("%Y-%m-%d")
    invoice_data_total_amount.text = str(invoice.invoice_data.total_amount)

    _build_invoice_data_annotations(invoice_data, invoice)

    invoice_data_type = ElementTree.SubElement(invoice_data, "RodzajFaktury")

    invoice_data_type.text = invoice.invoice_data.invoice_type.value

    # region rows
    invoice_data_rows = ElementTree.SubElement(invoice_data, "FaWiersze")
    invoice_data_rows_count = ElementTree.SubElement(invoice_data_rows, "LiczbaWierszyFaktury")
    # TODO: What is 'WartoscWierszyFaktury1 seen in webinar? https://www.youtube.com/watch?v=dnBGO6IPtzA

    invoice_data_rows_count.text = str(len(invoice.invoice_data.invoice_rows.rows))

    for index, row in enumerate(invoice.invoice_data.invoice_rows.rows, start=1):
        invoice_data_row = ElementTree.SubElement(invoice_data_rows, "FaWiersz")
        invoice_data_row_number = ElementTree.SubElement(invoice_data_row, "NrWierszaFa")
        invoice_data_row_name = ElementTree.SubElement(invoice_data_row, "P_7")
        invoice_data_row_tax_rate = ElementTree.SubElement(invoice_data_row, "P_12")

        invoice_data_row_number.text = str(index)
        invoice_data_row_name.text = row.name
        invoice_data_row_tax_rate.text = str(row.tax)
    # endregion
    # endregion


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

    _build_header(root, invoicing_software_name)
    _build_issuer(root, invoice)
    _build_receiver(root, invoice)
    _build_invoice_data(root, invoice)

    return cast(bytes, ElementTree.tostring(root, encoding="utf-8", xml_declaration=True))
