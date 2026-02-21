"""XML converters used to convert library models into KSEF-compliant XML files."""
from datetime import datetime, timezone
from typing import Optional, cast
from xml.etree import ElementTree

from ksef.models.invoice import (
    EuVatIdentification,
    ForeignIdentification,
    Invoice,
    NipIdentification,
    NoIdentification,
)

# FA(3) schema namespace
FA3_NAMESPACE = "http://crd.gov.pl/wzor/2025/06/25/13775/"
FA3_SCHEMA_LOCATION = (
    "http://crd.gov.pl/wzor/2025/06/25/13775/ http://crd.gov.pl/wzor/2025/06/25/13775/schemat.xsd"
)


def _build_header(
    root: ElementTree.Element,
    invoicing_software_name: str,
    creation_datetime: Optional[datetime] = None,
) -> None:
    header = ElementTree.SubElement(root, "Naglowek")
    form_code = ElementTree.SubElement(
        header,
        "KodFormularza",
        attrib={"kodSystemowy": "FA (3)", "wersjaSchemy": "1-0E"},
    )
    form_variant = ElementTree.SubElement(header, "WariantFormularza")
    creation_date = ElementTree.SubElement(header, "DataWytworzeniaFa")
    system_info = ElementTree.SubElement(header, "SystemInfo")

    form_code.text = "FA"
    form_variant.text = "3"
    # Use provided datetime or current time
    dt = creation_datetime or datetime.now(tz=timezone.utc)
    creation_date.text = dt.strftime("%Y-%m-%dT%H:%M:%S")
    system_info.text = invoicing_software_name


def _build_issuer(root: ElementTree.Element, invoice: Invoice) -> None:
    issuer = ElementTree.SubElement(root, "Podmiot1")

    issuer_id_data = ElementTree.SubElement(issuer, "DaneIdentyfikacyjne")
    issuer_nip = ElementTree.SubElement(issuer_id_data, "NIP")
    issuer_nip.text = invoice.issuer.identification_data.nip
    issuer_full_name = ElementTree.SubElement(issuer_id_data, "Nazwa")
    issuer_full_name.text = invoice.issuer.identification_data.full_name

    issuer_address = ElementTree.SubElement(issuer, "Adres", attrib={"xsi:type": "tns:TAdres"})
    issuer_country_code = ElementTree.SubElement(issuer_address, "KodKraju")
    issuer_country_code.text = invoice.issuer.address.country_code

    # AdresL1: street + house number (+ apartment number)
    addr = invoice.issuer.address
    address_l1 = f"{addr.street} {addr.house_number}"
    if addr.apartment_number is not None:
        address_l1 += f"/{addr.apartment_number}"
    issuer_address_l1 = ElementTree.SubElement(issuer_address, "AdresL1")
    issuer_address_l1.text = address_l1

    # AdresL2: postal code + city
    issuer_address_l2 = ElementTree.SubElement(issuer_address, "AdresL2")
    issuer_address_l2.text = f"{addr.postal_code} {addr.city}"


def _build_receiver(root: ElementTree.Element, invoice: Invoice) -> None:
    receiver = ElementTree.SubElement(root, "Podmiot2")
    receiver_id_data = ElementTree.SubElement(receiver, "DaneIdentyfikacyjne")

    id_data = invoice.recipient.identification_data
    if isinstance(id_data, NipIdentification):
        nip_el = ElementTree.SubElement(receiver_id_data, "NIP")
        nip_el.text = id_data.nip
    elif isinstance(id_data, EuVatIdentification):
        kod_ue = ElementTree.SubElement(receiver_id_data, "KodUE")
        kod_ue.text = id_data.eu_country_code
        nr_vat = ElementTree.SubElement(receiver_id_data, "NrVatUE")
        nr_vat.text = id_data.eu_vat_number
    elif isinstance(id_data, ForeignIdentification):
        if id_data.country_code is not None:
            kod_kraju = ElementTree.SubElement(receiver_id_data, "KodKraju")
            kod_kraju.text = id_data.country_code
        nr_id = ElementTree.SubElement(receiver_id_data, "NrID")
        nr_id.text = id_data.tax_id
    elif isinstance(id_data, NoIdentification):
        brak_id = ElementTree.SubElement(receiver_id_data, "BrakID")
        brak_id.text = "1"

    if invoice.recipient.name is not None:
        nazwa = ElementTree.SubElement(receiver, "Nazwa")
        nazwa.text = invoice.recipient.name

    if invoice.recipient.address is not None:
        addr = invoice.recipient.address
        receiver_address = ElementTree.SubElement(
            receiver, "Adres", attrib={"xsi:type": "tns:TAdres"}
        )
        receiver_country_code = ElementTree.SubElement(receiver_address, "KodKraju")
        receiver_country_code.text = addr.country_code

        address_l1 = f"{addr.street} {addr.house_number}"
        if addr.apartment_number is not None:
            address_l1 += f"/{addr.apartment_number}"
        receiver_address_l1 = ElementTree.SubElement(receiver_address, "AdresL1")
        receiver_address_l1.text = address_l1

        receiver_address_l2 = ElementTree.SubElement(receiver_address, "AdresL2")
        receiver_address_l2.text = f"{addr.postal_code} {addr.city}"

    receiver_jst = ElementTree.SubElement(receiver, "JST")
    receiver_jst.text = str(invoice.recipient.jst)
    receiver_gv = ElementTree.SubElement(receiver, "GV")
    receiver_gv.text = str(invoice.recipient.gv)


def _build_invoice_data_annotations(invoice_data: ElementTree.Element, invoice: Invoice) -> None:
    annotations = ElementTree.SubElement(invoice_data, "Adnotacje")
    data = invoice.invoice_data.invoice_annotations

    # P_16 - metoda kasowa
    p16 = ElementTree.SubElement(annotations, "P_16")
    p16.text = data.tax_settlement_on_payment.value

    # P_17 - samofakturowanie
    p17 = ElementTree.SubElement(annotations, "P_17")
    p17.text = data.self_invoice.value

    # P_18 - odwrotne obciążenie
    p18 = ElementTree.SubElement(annotations, "P_18")
    p18.text = data.reverse_charge.value

    # P_18A - mechanizm podzielonej płatności
    p18a = ElementTree.SubElement(annotations, "P_18A")
    p18a.text = data.split_payment.value

    # Zwolnienie - wrapper for P_19/P_19N
    zwolnienie = ElementTree.SubElement(annotations, "Zwolnienie")
    if data.free_from_vat.value == "1":
        p19 = ElementTree.SubElement(zwolnienie, "P_19")
        p19.text = "1"
    else:
        p19n = ElementTree.SubElement(zwolnienie, "P_19N")
        p19n.text = "1"

    # NoweSrodkiTransportu - wrapper for P_22/P_22N
    nst = ElementTree.SubElement(annotations, "NoweSrodkiTransportu")
    if data.intra_community_supply_of_new_transport_methods.value == "1":
        p22 = ElementTree.SubElement(nst, "P_22")
        p22.text = "1"
        p42_5 = ElementTree.SubElement(nst, "P_42_5")
        p42_5.text = "2"
    else:
        p22n = ElementTree.SubElement(nst, "P_22N")
        p22n.text = "1"

    # P_23 - procedura uproszczona
    p23 = ElementTree.SubElement(annotations, "P_23")
    p23.text = data.simplified_procedure_by_second_tax_payer.value

    # PMarzy - wrapper for P_PMarzy/P_PMarzyN
    pmarzy = ElementTree.SubElement(annotations, "PMarzy")
    if data.margin_procedure.value == "1":
        p_pm = ElementTree.SubElement(pmarzy, "P_PMarzy")
        p_pm.text = "1"
    else:
        p_pmn = ElementTree.SubElement(pmarzy, "P_PMarzyN")
        p_pmn.text = "1"


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

    for index, row in enumerate(invoice.invoice_data.invoice_rows.rows, start=1):
        invoice_data_row = ElementTree.SubElement(invoice_data, "FaWiersz")
        invoice_data_row_number = ElementTree.SubElement(invoice_data_row, "NrWierszaFa")
        invoice_data_row_name = ElementTree.SubElement(invoice_data_row, "P_7")
        invoice_data_row_tax_rate = ElementTree.SubElement(invoice_data_row, "P_12")

        invoice_data_row_number.text = str(index)
        invoice_data_row_name.text = row.name
        invoice_data_row_tax_rate.text = str(row.tax)


def convert_invoice_to_xml(invoice: Invoice, invoicing_software_name: str = "python-ksef") -> bytes:
    """Convert an invoice model instance to XML document representing this invoice.

    Uses FA(3) schema format (http://crd.gov.pl/wzor/2025/06/25/13775/).
    """
    root = ElementTree.Element(
        "Faktura",
        attrib={
            "xmlns": FA3_NAMESPACE,
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:tns": FA3_NAMESPACE,
            "xsi:schemaLocation": FA3_SCHEMA_LOCATION,
        },
    )

    _build_header(root, invoicing_software_name, invoice.creation_datetime)
    _build_issuer(root, invoice)
    _build_receiver(root, invoice)
    _build_invoice_data(root, invoice)

    return cast(bytes, ElementTree.tostring(root, encoding="utf-8", xml_declaration=True))
