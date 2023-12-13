"""Builder for InitSessionTokenRequest xml document."""
from typing import cast
from xml.dom import minidom

from ksef.models.responses.authorization_challenge import AuthorizationChallenge


class InitSessionTokenRequestBuilder:
    """Builder used to construct a XML request for initializing a session token."""

    NS = "http://ksef.mf.gov.pl/schema/gtw/svc/online/types/2021/10/01/0001"
    NS2 = "http://ksef.mf.gov.pl/schema/gtw/svc/types/2021/10/01/0001"
    NS3 = "http://ksef.mf.gov.pl/schema/gtw/svc/online/auth/request/2021/10/01/0001"
    XSI = "http://www.w3.org/2001/XMLSchema-instance"

    def __init__(
        self, authorization_challenge: AuthorizationChallenge, nip: str, encrypted_token: str
    ):
        self.authorization_challenge = authorization_challenge
        self.nip = nip
        self.encrypted_token = encrypted_token

    @staticmethod
    def _build_document_type_element(root: minidom.Document) -> minidom.Element:
        document_type = root.createElement("DocumentType")
        service = root.createElement("ns2:Service")
        service.appendChild(root.createTextNode("KSeF"))
        document_type.appendChild(service)

        form_code = root.createElement("ns2:FormCode")
        document_type.appendChild(form_code)

        system_code = root.createElement("ns2:SystemCode")
        system_code.appendChild(root.createTextNode("FA (1)"))
        form_code.appendChild(system_code)
        schema_version = root.createElement("ns2:SchemaVersion")
        schema_version.appendChild(root.createTextNode("1-0E"))
        form_code.appendChild(schema_version)
        target_namespace = root.createElement("ns2:TargetNamespace")
        target_namespace.appendChild(
            root.createTextNode("http://crd.gov.pl/wzor/2021/11/29/11089/")
        )
        form_code.appendChild(target_namespace)
        value = root.createElement("ns2:Value")
        value.appendChild(root.createTextNode("FA"))
        form_code.appendChild(value)

        return document_type

    def _build_token_element(self, root: minidom.Document) -> minidom.Element:
        token = root.createElement("Token")
        token.appendChild(root.createTextNode(self.encrypted_token))
        return token

    def _build_context_element(self, root: minidom.Document) -> minidom.Element:
        context = root.createElement("ns3:Context")

        challenge = root.createElement("Challenge")
        challenge.appendChild(root.createTextNode(self.authorization_challenge.challenge))
        context.appendChild(challenge)

        identifier = root.createElement("Identifier")
        identifier.setAttribute("xmlns:xsi", self.XSI)
        identifier.setAttribute("xsi:type", "ns2:SubjectIdentifierByCompanyType")

        identifier_inner = root.createElement("ns2:Identifier")
        identifier_inner.appendChild(root.createTextNode(self.nip))
        identifier.appendChild(identifier_inner)
        context.appendChild(identifier)

        context.appendChild(self._build_document_type_element(root=root))
        context.appendChild(self._build_token_element(root=root))

        return context

    def _build_signature_element(self, root: minidom.Document) -> minidom.Element:
        signature = root.createElement("Signature")
        signature.setAttribute("xmlns", "http://www.w3.org/2000/09/xmldsig#")

        signed_info = root.createElement("SignedInfo")

        canonicalization_method = root.createElement("CanonicalizationMethod")
        canonicalization_method.setAttribute(
            "Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
        )
        signed_info.appendChild(canonicalization_method)

        signature_method = root.createElement("SignatureMethod")
        signature_method.setAttribute("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")
        signed_info.appendChild(signature_method)

        reference = root.createElement("Reference")
        reference.setAttribute("URI", "")
        signed_info.appendChild(reference)

        transforms = root.createElement("Transforms")
        reference.appendChild(transforms)

        transform = root.createElement("Transform")
        transform.setAttribute("Algorithm", "http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        transforms.appendChild(transform)

        digest_method = root.createElement("DigestMethod")
        digest_method.setAttribute("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")
        reference.appendChild(digest_method)

        digest_value = root.createElement("DigestValue")
        calculated_digest_value = "XXX"  # TODO
        digest_value.appendChild(root.createTextNode(calculated_digest_value))
        reference.appendChild(digest_value)

        signature.appendChild(signed_info)

        calculated_signature_value = "XXX"  # TODO
        signature_value = root.createElement("SignatureValue")
        signature_value.appendChild(root.createTextNode(calculated_signature_value))

        signature.appendChild(signature_value)

        key_info = root.createElement("KeyInfo")
        signature.appendChild(key_info)

        x509_data = root.createElement("X509Data")
        key_info.appendChild(x509_data)

        calculated_x509_certificate = "XXX"  # TODO
        x509_certificate = root.createElement("X509Certificate")
        x509_certificate.appendChild(root.createTextNode(calculated_x509_certificate))
        x509_data.appendChild(x509_certificate)
        return signature

    def build_xml(self) -> str:
        """Build and return an XML string representing a request to initialize a session token."""
        root = minidom.Document()

        document = root.createElement("ns3:InitSessionTokenRequest")
        document.setAttribute("xmlns", self.NS)
        document.setAttribute("xmlns:ns2", self.NS2)
        document.setAttribute("xmlns:ns3", self.NS3)
        root.appendChild(document)

        context = self._build_context_element(root=root)
        document.appendChild(context)

        return cast(str, root.toprettyxml(indent="    ", encoding="UTF-8").decode("utf-8"))
