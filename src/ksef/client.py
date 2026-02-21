"""Base client for interacting with the KSEF API."""
import base64
import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Union, cast
from urllib.parse import urlencode, urljoin

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from ksef.auth.base import Authorization
from ksef.constants import (
    URL_INVOICES_GET,
    URL_PUBLIC_KEY_CERTS,
    URL_QUERY_INVOICES,
    URL_SESSIONS_INVOICES,
    URL_SESSIONS_INVOICES_STATUS,
    URL_SESSIONS_ONLINE,
    URL_SESSIONS_ONLINE_CLOSE,
    URL_SESSIONS_ONLINE_INVOICES,
    URL_SESSIONS_STATUS,
    Environment,
)
from ksef.models.invoice import Invoice
from ksef.models.responses.session import (
    CloseSessionResponse,
    RawResponse,
    SendInvoiceResponse,
    SessionInvoiceStatusResponse,
    SessionStatusResponse,
)
from ksef.xml_converters import FA3_NAMESPACE, convert_invoice_to_xml

logger = logging.getLogger(__name__)

AES_KEY_SIZE = 32  # 256 bits
AES_BLOCK_SIZE = 128  # bits
IV_SIZE = 16  # bytes


@dataclass
class SessionContext:
    """Context for an active KSEF online session."""

    reference_number: str
    aes_key: bytes
    iv: bytes


class Client:
    """Base client for interacting with the KSEF API."""

    def __init__(
        self,
        authorization: Authorization,
        environment: Environment = Environment.PRODUCTION,
    ):
        self.authorization = authorization
        self.environment = environment
        self.base_url = environment.value
        self.session = requests.Session()

    def build_url(self, url: str, params: Optional[Mapping[str, Union[str, int]]] = None) -> str:
        """Construct a full URL."""
        url = urljoin(base=self.base_url, url=url)
        if params is not None:
            param_str = urlencode(params)
            return f"{url}?{param_str}"

        return url

    def _auth_headers(self) -> Dict[str, str]:
        """Build authorization headers using the Bearer access token."""
        return {"Authorization": f"Bearer {self.authorization.get_access_token()}"}

    def _fetch_symmetric_key_cert(self) -> RSAPublicKey:
        """Fetch the SymmetricKeyEncryption public key from KSEF."""
        response = self.session.get(
            url=self.build_url(URL_PUBLIC_KEY_CERTS),
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        certs: List[Dict[str, Any]] = response.json()

        for cert in certs:
            usages = cert.get("usage", [])
            if "SymmetricKeyEncryption" in usages:
                cert_b64 = cert["certificate"]
                cert_der = base64.b64decode(cert_b64)
                x509_cert = x509.load_der_x509_certificate(cert_der)
                public_key = x509_cert.public_key()
                return cast(RSAPublicKey, public_key)

        raise ValueError("No SymmetricKeyEncryption certificate found")

    def _encrypt_aes_key(self, aes_key: bytes, public_key: RSAPublicKey) -> bytes:
        """Encrypt AES key using RSA-OAEP."""
        return public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def _encrypt_invoice_xml(self, invoice_xml: bytes, aes_key: bytes, iv: bytes) -> bytes:
        """Encrypt invoice XML using AES-256-CBC."""
        padder = PKCS7(AES_BLOCK_SIZE).padder()
        padded_data = padder.update(invoice_xml) + padder.finalize()

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padded_data) + encryptor.finalize()

    def search_invoices(self, page_size: int = 100, page_offset: int = 0) -> Dict[str, str]:
        """Search for invoices with the specified page size and offset."""
        params = {
            "PageSize": page_size,
            "PageOffset": page_offset,
        }
        response = self.session.post(
            url=self.build_url(url=URL_QUERY_INVOICES, params=params),
            headers={
                "Accept": "application/json",
                **self._auth_headers(),
            },
            json={
                "queryCriteria": {
                    "subjectType": "subject1",
                    "type": "range",
                    "invoicingDateFrom": "2023-11-14T13:21:09.000Z",
                    "invoicingDateTo": "2023-12-12T13:21:09.000Z",
                }
            },
        )
        logger.debug("Search invoices response (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        data = cast(Dict[str, str], response.json())
        return data

    def open_session(self, nip: str) -> SessionContext:
        """Open an online session for invoice submission.

        Parameters
        ----------
        nip : str
            The NIP (tax identification number) to open the session for.

        Returns
        -------
        SessionContext
            Contains session reference number and encryption keys for sending invoices.
        """
        # Fetch the encryption public key
        public_key = self._fetch_symmetric_key_cert()

        # Generate AES key and IV
        aes_key = os.urandom(AES_KEY_SIZE)
        iv = os.urandom(IV_SIZE)

        # Encrypt the AES key with RSA-OAEP
        encrypted_key = self._encrypt_aes_key(aes_key, public_key)

        response = self.session.post(
            url=self.build_url(url=URL_SESSIONS_ONLINE),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self._auth_headers(),
            },
            json={
                "contextIdentifier": {
                    "type": "Nip",
                    "value": nip,
                },
                "formCode": {
                    "systemCode": "FA (3)",
                    "schemaVersion": "1-0E",
                    "targetNamespace": FA3_NAMESPACE,
                    "value": "FA",
                },
                "encryption": {
                    "type": "AES",
                    "encryptedSymmetricKey": base64.b64encode(encrypted_key).decode(),
                    "initializationVector": base64.b64encode(iv).decode(),
                },
            },
        )
        logger.debug("Open session response (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        data = response.json()

        return SessionContext(
            reference_number=data["referenceNumber"],
            aes_key=aes_key,
            iv=iv,
        )

    def send_invoice_in_session(
        self,
        session_context: SessionContext,
        invoice: Invoice,
    ) -> SendInvoiceResponse:
        """Send an encrypted invoice within an active session.

        Parameters
        ----------
        session_context : SessionContext
            The session context from open_session().
        invoice : Invoice
            The invoice to send.

        Returns
        -------
        SendInvoiceResponse
            Contains reference numbers and processing status.
        """
        # Convert invoice to XML
        invoice_xml = convert_invoice_to_xml(invoice)

        # Encrypt the invoice XML using the session's AES key
        encrypted_invoice = self._encrypt_invoice_xml(
            invoice_xml, session_context.aes_key, session_context.iv
        )

        # Calculate hashes
        invoice_hash = base64.b64encode(hashlib.sha256(invoice_xml).digest()).decode()
        encrypted_hash = base64.b64encode(hashlib.sha256(encrypted_invoice).digest()).decode()

        url = URL_SESSIONS_ONLINE_INVOICES.format(reference_number=session_context.reference_number)
        response = self.session.post(
            url=self.build_url(url=url),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self._auth_headers(),
            },
            json={
                "invoiceHash": invoice_hash,
                "invoiceSize": len(invoice_xml),
                "encryptedInvoiceHash": encrypted_hash,
                "encryptedInvoiceSize": len(encrypted_invoice),
                "encryptedInvoiceContent": base64.b64encode(encrypted_invoice).decode(),
                "offlineMode": False,
            },
        )
        logger.debug(
            "Send invoice in session response (%s): %s", response.status_code, response.text
        )
        response.raise_for_status()
        response_data = response.json()
        send_response = SendInvoiceResponse.from_dict(response_data)
        send_response.session_reference_number = session_context.reference_number
        send_response.invoice_xml = invoice_xml
        send_response.raw_response = RawResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response_data,
        )
        return send_response

    def close_session(self, session_context: SessionContext) -> CloseSessionResponse:
        """Close an active online session.

        Parameters
        ----------
        session_context : SessionContext
            The session context from open_session().

        Returns
        -------
        CloseSessionResponse
            Contains the session reference number.
        """
        url = URL_SESSIONS_ONLINE_CLOSE.format(reference_number=session_context.reference_number)
        response = self.session.post(
            url=self.build_url(url=url),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self._auth_headers(),
            },
            json={},
        )
        logger.debug("Close session response (%s): %s", response.status_code, response.text)
        # Close session returns 204 No Content on success
        if response.status_code == 204:  # noqa: PLR2004
            return CloseSessionResponse(reference_number=session_context.reference_number)
        response.raise_for_status()
        return CloseSessionResponse.from_dict(response.json())

    def send_invoice(self, nip: str, invoice: Invoice) -> SendInvoiceResponse:
        """Send a single invoice (handles session lifecycle automatically).

        This convenience method opens a session, sends the invoice, and closes
        the session automatically.

        Parameters
        ----------
        nip : str
            The NIP (tax identification number) to send the invoice for.
        invoice : Invoice
            The invoice to send.

        Returns
        -------
        SendInvoiceResponse
            Contains reference numbers and processing status.
        """
        # Open session
        session_context = self.open_session(nip)

        try:
            # Send invoice
            send_response = self.send_invoice_in_session(
                session_context=session_context,
                invoice=invoice,
            )
            return send_response
        finally:
            # Always close session
            self.close_session(session_context)

    def get_session_status(self, session_reference_number: str) -> SessionStatusResponse:
        """Get the status of a session.

        Parameters
        ----------
        session_reference_number : str
            The session reference number from open_session() or SendInvoiceResponse.

        Returns
        -------
        SessionStatusResponse
            Contains overall session status and invoice counts.
        """
        url = URL_SESSIONS_STATUS.format(reference_number=session_reference_number)
        response = self.session.get(
            url=self.build_url(url=url),
            headers={
                "Accept": "application/json",
                **self._auth_headers(),
            },
        )
        logger.debug("Get session status response (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        return SessionStatusResponse.from_dict(response.json())

    def get_session_invoices(
        self, session_reference_number: str, page_size: int = 10
    ) -> list[SessionInvoiceStatusResponse]:
        """Get the status of all invoices in a session.

        Parameters
        ----------
        session_reference_number : str
            The session reference number.
        page_size : int
            Number of results per page (default 10).

        Returns
        -------
        list[SessionInvoiceStatusResponse]
            List of invoice statuses for the session.
        """
        url = URL_SESSIONS_INVOICES.format(reference_number=session_reference_number)
        response = self.session.get(
            url=self.build_url(url=url, params={"PageSize": page_size}),
            headers={
                "Accept": "application/json",
                **self._auth_headers(),
            },
        )
        logger.debug("Get session invoices response (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        data = response.json()
        return [SessionInvoiceStatusResponse.from_dict(item) for item in data]

    def get_invoice_status(
        self, session_reference_number: str, invoice_reference_number: str
    ) -> SessionInvoiceStatusResponse:
        """Get the status of a specific invoice in a session.

        Parameters
        ----------
        session_reference_number : str
            The session reference number.
        invoice_reference_number : str
            The invoice reference number from SendInvoiceResponse.

        Returns
        -------
        SessionInvoiceStatusResponse
            The invoice status including processing result.
        """
        url = URL_SESSIONS_INVOICES_STATUS.format(
            reference_number=session_reference_number,
            invoice_reference_number=invoice_reference_number,
        )
        response = self.session.get(
            url=self.build_url(url=url),
            headers={
                "Accept": "application/json",
                **self._auth_headers(),
            },
        )
        logger.debug("Get invoice status response (%s): %s", response.status_code, response.text)
        response.raise_for_status()
        return SessionInvoiceStatusResponse.from_dict(response.json())

    def download_invoice(self, ksef_reference_number: str) -> bytes:
        """Download invoice XML by KSEF reference number.

        Parameters
        ----------
        ksef_reference_number : str
            The KSEF reference number of the invoice to download.

        Returns
        -------
        bytes
            The invoice XML content.
        """
        url = URL_INVOICES_GET.format(ksef_reference_number=ksef_reference_number)
        response = self.session.get(
            url=self.build_url(url=url),
            headers={
                "Accept": "application/xml",
                **self._auth_headers(),
            },
        )
        logger.debug(
            "Download invoice response (%s): %s bytes",
            response.status_code,
            len(response.content),
        )
        response.raise_for_status()
        return response.content
