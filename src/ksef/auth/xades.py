"""XAdES Signature-based authorization implementation for API v2."""
import base64
import copy
import hashlib
import logging
import time
import uuid
from typing import Mapping, Optional, Tuple
from urllib.parse import urljoin

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa, utils
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.x509 import Certificate, load_der_x509_certificate, load_pem_x509_certificate
from lxml import etree

from ksef.auth.base import Authorization
from ksef.constants import (
    DEFAULT_HEADERS,
    TIMEOUT,
    URL_AUTH_CHALLENGE,
    URL_AUTH_STATUS,
    URL_AUTH_TOKEN_REDEEM,
    URL_AUTH_XADES_SIGNATURE,
    Environment,
)
from ksef.exceptions import AuthenticationError
from ksef.models.responses.auth import AuthChallenge, AuthStatus, AuthTokens, SignatureResponse
from ksef.utils import response_to_exception

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 1.0
_POLL_MAX_ATTEMPTS = 60

_NS_DS = "http://www.w3.org/2000/09/xmldsig#"
_NS_XADES = "http://uri.etsi.org/01903/v1.3.2#"
_C14N_ALGO = "http://www.w3.org/2001/10/xml-exc-c14n#"
_SIG_ALGO_RSA = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
_SIG_ALGO_ECDSA = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256"
_DIGEST_ALGO = "http://www.w3.org/2001/04/xmlenc#sha256"
_TRANSFORM_ENVELOPED = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"


def _build_signed_info(
    signature: etree._Element, signed_props_id: str, sig_algo: str
) -> Tuple[etree._Element, etree._Element, etree._Element]:
    """Build the SignedInfo element with document and SignedProperties references.

    Returns (signed_info, digest_value_doc, digest_value_sp).
    """
    signed_info = etree.SubElement(signature, "{%s}SignedInfo" % _NS_DS)
    c14n_method = etree.SubElement(signed_info, "{%s}CanonicalizationMethod" % _NS_DS)
    c14n_method.set("Algorithm", _C14N_ALGO)
    sig_method = etree.SubElement(signed_info, "{%s}SignatureMethod" % _NS_DS)
    sig_method.set("Algorithm", sig_algo)

    # Reference to document (enveloped)
    ref_doc = etree.SubElement(signed_info, "{%s}Reference" % _NS_DS)
    ref_doc.set("URI", "")
    transforms = etree.SubElement(ref_doc, "{%s}Transforms" % _NS_DS)
    transform_env = etree.SubElement(transforms, "{%s}Transform" % _NS_DS)
    transform_env.set("Algorithm", _TRANSFORM_ENVELOPED)
    transform_c14n = etree.SubElement(transforms, "{%s}Transform" % _NS_DS)
    transform_c14n.set("Algorithm", _C14N_ALGO)
    digest_method_doc = etree.SubElement(ref_doc, "{%s}DigestMethod" % _NS_DS)
    digest_method_doc.set("Algorithm", _DIGEST_ALGO)
    digest_value_doc = etree.SubElement(ref_doc, "{%s}DigestValue" % _NS_DS)

    # Reference to SignedProperties
    ref_sp = etree.SubElement(signed_info, "{%s}Reference" % _NS_DS)
    ref_sp.set("URI", f"#{signed_props_id}")
    ref_sp.set("Type", "http://uri.etsi.org/01903#SignedProperties")
    transforms_sp = etree.SubElement(ref_sp, "{%s}Transforms" % _NS_DS)
    transform_sp_c14n = etree.SubElement(transforms_sp, "{%s}Transform" % _NS_DS)
    transform_sp_c14n.set("Algorithm", _C14N_ALGO)
    digest_method_sp = etree.SubElement(ref_sp, "{%s}DigestMethod" % _NS_DS)
    digest_method_sp.set("Algorithm", _DIGEST_ALGO)
    digest_value_sp = etree.SubElement(ref_sp, "{%s}DigestValue" % _NS_DS)

    return signed_info, digest_value_doc, digest_value_sp


def _build_xades_object(  # noqa: PLR0913
    signature: etree._Element,
    sig_id: str,
    signed_props_id: str,
    cert_digest: str,
    issuer_name: str,
    serial_number: int,
) -> etree._Element:
    """Build the XAdES Object/QualifyingProperties/SignedProperties elements.

    Returns the SignedProperties element.
    """
    obj = etree.SubElement(signature, "{%s}Object" % _NS_DS)
    qp = etree.SubElement(
        obj,
        "{%s}QualifyingProperties" % _NS_XADES,
        nsmap={"xades": _NS_XADES},
    )
    qp.set("Target", f"#{sig_id}")
    signed_properties = etree.SubElement(qp, "{%s}SignedProperties" % _NS_XADES)
    signed_properties.set("Id", signed_props_id)
    ssp = etree.SubElement(signed_properties, "{%s}SignedSignatureProperties" % _NS_XADES)
    signing_cert_el = etree.SubElement(ssp, "{%s}SigningCertificate" % _NS_XADES)
    cert_ref = etree.SubElement(signing_cert_el, "{%s}Cert" % _NS_XADES)
    cert_digest_el = etree.SubElement(cert_ref, "{%s}CertDigest" % _NS_XADES)
    dm = etree.SubElement(cert_digest_el, "{%s}DigestMethod" % _NS_DS)
    dm.set("Algorithm", _DIGEST_ALGO)
    dv = etree.SubElement(cert_digest_el, "{%s}DigestValue" % _NS_DS)
    dv.text = cert_digest
    issuer_serial = etree.SubElement(cert_ref, "{%s}IssuerSerial" % _NS_XADES)
    x509_issuer = etree.SubElement(issuer_serial, "{%s}X509IssuerName" % _NS_DS)
    x509_issuer.text = issuer_name
    x509_serial = etree.SubElement(issuer_serial, "{%s}X509SerialNumber" % _NS_DS)
    x509_serial.text = str(serial_number)
    return signed_properties


class XadesAuthorization(Authorization):
    """XAdES Signature-based authorization for API v2."""

    def __init__(  # noqa: PLR0913
        self,
        signing_cert: bytes,
        private_key: bytes,
        environment: Environment = Environment.PRODUCTION,
        timeout: int = TIMEOUT,
        key_password: Optional[bytes] = None,
    ):
        self._signing_cert = signing_cert
        self._private_key_bytes = private_key
        self._key_password = key_password
        self.environment = environment
        self.base_url = environment.value
        self.timeout = timeout

    def authorize(self, nip: str) -> AuthTokens:
        """Perform the full v2 XAdES authorization flow.

        Parameters
        ----------
        nip : str
            The NIP (tax identification number) to authorize with.
        """
        challenge = self._get_challenge()
        signed_xml = self._build_and_sign_request(challenge=challenge, nip=nip)
        signature_response = self._submit_xades(signed_xml=signed_xml)
        self._poll_auth_status(
            reference_number=signature_response.reference_number,
            authentication_token=signature_response.authentication_token.token,
        )
        tokens = self._redeem_token(
            authentication_token=signature_response.authentication_token.token,
        )
        self._tokens = tokens
        return tokens

    def build_url(self, url: str) -> str:
        """Construct a full URL."""
        return urljoin(base=self.base_url, url=url)

    @staticmethod
    def build_headers(**optional: str) -> Mapping[str, str]:
        """Construct headers."""
        headers = copy.deepcopy(DEFAULT_HEADERS)
        headers.update(optional)
        return headers

    def _get_challenge(self) -> AuthChallenge:
        """Get the authorization challenge."""
        response = requests.post(
            url=self.build_url(URL_AUTH_CHALLENGE),
            headers=self.build_headers(),
            json={},
            timeout=self.timeout,
        )
        logger.debug(
            "Authorization challenge response (%s): %s", response.status_code, response.text
        )
        error = response_to_exception(response)
        if error is not None:
            raise error
        return AuthChallenge.from_dict(response.json())

    def _load_private_key(self) -> "rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey":
        """Load the private key (RSA or EC) from PEM or DER bytes."""
        try:
            key = serialization.load_pem_private_key(
                self._private_key_bytes, password=self._key_password
            )
        except (ValueError, TypeError):
            key = serialization.load_der_private_key(
                self._private_key_bytes, password=self._key_password
            )
        if not isinstance(key, (rsa.RSAPrivateKey, ec.EllipticCurvePrivateKey)):
            raise AuthenticationError("Private key must be an RSA or EC key.")
        return key

    def _load_certificate(self) -> Certificate:
        """Load the X.509 certificate from PEM or DER bytes."""
        try:
            return load_pem_x509_certificate(self._signing_cert)
        except ValueError:
            return load_der_x509_certificate(self._signing_cert)

    def _build_and_sign_request(self, challenge: AuthChallenge, nip: str) -> bytes:
        """Build AuthTokenRequest XML and sign with XAdES-BES."""
        ns_auth = "http://ksef.mf.gov.pl/auth/token/2.0"

        root = etree.Element(
            "{%s}AuthTokenRequest" % ns_auth,
            nsmap={None: ns_auth},
        )
        challenge_el = etree.SubElement(root, "{%s}Challenge" % ns_auth)
        challenge_el.text = challenge.challenge

        context_id = etree.SubElement(root, "{%s}ContextIdentifier" % ns_auth)
        nip_el = etree.SubElement(context_id, "{%s}Nip" % ns_auth)
        nip_el.text = nip

        subject_type = etree.SubElement(root, "{%s}SubjectIdentifierType" % ns_auth)
        subject_type.text = "certificateSubject"

        signed_xml = self._sign_xml(root)
        result: bytes = etree.tostring(signed_xml, xml_declaration=True, encoding="UTF-8")
        return result

    def _sign_xml(self, root: etree._Element) -> etree._Element:
        """Apply an XAdES-BES enveloped signature to the XML element."""
        private_key = self._load_private_key()
        cert = self._load_certificate()
        cert_der = cert.public_bytes(serialization.Encoding.DER)
        cert_b64 = base64.b64encode(cert_der).decode("ascii")
        cert_digest = base64.b64encode(hashlib.sha256(cert_der).digest()).decode("ascii")
        issuer_name = cert.issuer.rfc4514_string()
        serial_number = cert.serial_number

        sig_algo = _SIG_ALGO_RSA if isinstance(private_key, rsa.RSAPrivateKey) else _SIG_ALGO_ECDSA

        sig_id = f"Signature-{uuid.uuid4()}"
        signed_props_id = f"SignedProperties-{uuid.uuid4()}"

        nsmap_ds = {"ds": _NS_DS}

        # Build Signature element
        signature = etree.SubElement(root, "{%s}Signature" % _NS_DS, nsmap=nsmap_ds)
        signature.set("Id", sig_id)

        # Build SignedInfo with references
        signed_info, digest_value_doc, digest_value_sp = _build_signed_info(
            signature, signed_props_id, sig_algo
        )

        # SignatureValue placeholder
        signature_value = etree.SubElement(signature, "{%s}SignatureValue" % _NS_DS)

        # KeyInfo
        key_info = etree.SubElement(signature, "{%s}KeyInfo" % _NS_DS)
        x509_data = etree.SubElement(key_info, "{%s}X509Data" % _NS_DS)
        x509_cert = etree.SubElement(x509_data, "{%s}X509Certificate" % _NS_DS)
        x509_cert.text = cert_b64

        # Build XAdES QualifyingProperties
        signed_properties = _build_xades_object(
            signature, sig_id, signed_props_id, cert_digest, issuer_name, serial_number
        )

        # Compute digest of SignedProperties (c14n)
        sp_c14n = etree.tostring(signed_properties, method="c14n", exclusive=True)
        sp_digest = base64.b64encode(hashlib.sha256(sp_c14n).digest()).decode("ascii")
        digest_value_sp.text = sp_digest

        # Compute digest of document (without Signature element)
        sig_parent = signature.getparent()
        if sig_parent is None:
            raise AuthenticationError("Signature element has no parent.")
        sig_parent.remove(signature)
        doc_c14n = etree.tostring(sig_parent, method="c14n", exclusive=True)
        doc_digest = base64.b64encode(hashlib.sha256(doc_c14n).digest()).decode("ascii")
        digest_value_doc.text = doc_digest
        sig_parent.append(signature)

        # Compute SignatureValue
        si_c14n = etree.tostring(signed_info, method="c14n", exclusive=True)
        if isinstance(private_key, rsa.RSAPrivateKey):
            sig_bytes = private_key.sign(si_c14n, asym_padding.PKCS1v15(), hashes.SHA256())
        else:
            # EC key — sign returns DER-encoded (r, s); XMLDSig expects raw r||s
            der_sig = private_key.sign(si_c14n, ec.ECDSA(hashes.SHA256()))
            (r, s) = utils.decode_dss_signature(der_sig)
            key_size_bytes = (private_key.key_size + 7) // 8
            sig_bytes = r.to_bytes(key_size_bytes, "big") + s.to_bytes(key_size_bytes, "big")
        signature_value.text = base64.b64encode(sig_bytes).decode("ascii")

        return root

    def _submit_xades(self, signed_xml: bytes) -> SignatureResponse:
        """Submit signed XML to POST /auth/xades-signature."""
        response = requests.post(
            url=self.build_url(URL_AUTH_XADES_SIGNATURE),
            headers={"Content-Type": "application/xml", "Accept": "application/json"},
            data=signed_xml,
            timeout=self.timeout,
        )
        logger.debug("XAdES signature response (%s): %s", response.status_code, response.text)
        error = response_to_exception(response)
        if error is not None:
            raise error
        return SignatureResponse.from_dict(response.json())

    def _poll_auth_status(
        self,
        reference_number: str,
        authentication_token: str,
    ) -> AuthStatus:
        """Poll GET /auth/{referenceNumber} until authentication completes."""
        url = self.build_url(URL_AUTH_STATUS.format(reference_number=reference_number))
        for attempt in range(_POLL_MAX_ATTEMPTS):
            response = requests.get(
                url=url,
                headers={
                    **self.build_headers(),
                    "Authorization": f"Bearer {authentication_token}",
                },
                timeout=self.timeout,
            )
            error = response_to_exception(response)
            if error is not None:
                raise error

            status = AuthStatus.from_dict(response.json())
            if status.status.code == 200:  # noqa: PLR2004
                return status

            logger.debug(
                "Auth status poll attempt %d: code=%d, desc=%s",
                attempt + 1,
                status.status.code,
                status.status.description,
            )
            time.sleep(_POLL_INTERVAL)

        raise AuthenticationError(
            f"Authentication polling timed out after {_POLL_MAX_ATTEMPTS} attempts."
        )

    def _redeem_token(self, authentication_token: str) -> AuthTokens:
        """Redeem authentication token for access/refresh tokens via POST /auth/token/redeem."""
        response = requests.post(
            url=self.build_url(URL_AUTH_TOKEN_REDEEM),
            headers={
                **self.build_headers(),
                "Authorization": f"Bearer {authentication_token}",
            },
            json={},
            timeout=self.timeout,
        )
        logger.debug("Token redeem response (%s): %s", response.status_code, response.text)
        error = response_to_exception(response)
        if error is not None:
            raise error
        return AuthTokens.from_dict(response.json())
