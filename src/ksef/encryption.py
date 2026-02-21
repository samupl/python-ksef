"""Invoice encryption for KSEF submission."""
import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

AES_KEY_SIZE = 32  # 256 bits
AES_BLOCK_SIZE = 128  # bits
IV_SIZE = 16  # bytes


@dataclass
class EncryptedInvoice:
    """Encrypted invoice content for KSEF submission."""

    encrypted_content: str  # Base64-encoded


def _pad_data(data: bytes) -> bytes:
    """Pad data using PKCS7 padding for AES block size."""
    padder = PKCS7(AES_BLOCK_SIZE).padder()
    return padder.update(data) + padder.finalize()


def _unpad_data(data: bytes) -> bytes:
    """Remove PKCS7 padding from data."""
    unpadder = PKCS7(AES_BLOCK_SIZE).unpadder()
    return unpadder.update(data) + unpadder.finalize()


def _encrypt_aes_cbc(data: bytes, key: bytes, iv: bytes) -> bytes:
    """Encrypt data using AES-256-CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padded_data = _pad_data(data)
    return encryptor.update(padded_data) + encryptor.finalize()


def _decrypt_aes_cbc(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt data using AES-256-CBC."""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    return _unpad_data(padded_data)


def _encrypt_key_rsa_oaep(key: bytes, public_key: RSAPublicKey) -> bytes:
    """Encrypt AES key using RSA-OAEP with SHA-256."""
    return public_key.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def _load_public_key_from_b64(public_key_b64: str) -> RSAPublicKey:
    """Load RSA public key from base64-encoded DER format."""
    public_key_der = base64.b64decode(public_key_b64)
    public_key = serialization.load_der_public_key(public_key_der)
    if not isinstance(public_key, RSAPublicKey):
        raise TypeError("Expected RSA public key")
    return public_key


def encrypt_invoice(invoice_xml: bytes, public_key_b64: str) -> EncryptedInvoice:
    """Encrypt invoice XML for KSEF submission.

    Parameters
    ----------
    invoice_xml : bytes
        The invoice XML content to encrypt.
    public_key_b64 : str
        Base64-encoded DER public key from session response.

    Returns
    -------
    EncryptedInvoice
        The encrypted invoice with base64-encoded content.
    """
    # Load the public key
    public_key = _load_public_key_from_b64(public_key_b64)

    # Generate random AES key and IV
    aes_key = os.urandom(AES_KEY_SIZE)
    iv = os.urandom(IV_SIZE)

    # Encrypt the invoice XML with AES-256-CBC
    ciphertext = _encrypt_aes_cbc(invoice_xml, aes_key, iv)

    # Encrypt the AES key with RSA-OAEP
    encrypted_key = _encrypt_key_rsa_oaep(aes_key, public_key)

    # Concatenate: encrypted_key || iv || ciphertext
    combined = encrypted_key + iv + ciphertext

    # Base64 encode
    encrypted_content = base64.b64encode(combined).decode("utf-8")

    return EncryptedInvoice(encrypted_content=encrypted_content)


def decrypt_invoice(
    encrypted_content: str,
    private_key_pem: bytes,
    key_size: int = 256,
) -> bytes:
    """Decrypt invoice XML (for testing purposes).

    Parameters
    ----------
    encrypted_content : str
        Base64-encoded encrypted invoice content.
    private_key_pem : bytes
        PEM-encoded RSA private key.
    key_size : int
        RSA key size in bytes (default 256 for 2048-bit key).

    Returns
    -------
    bytes
        The decrypted invoice XML.
    """
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

    # Decode base64
    combined = base64.b64decode(encrypted_content)

    # Split into components
    encrypted_key = combined[:key_size]
    iv = combined[key_size : key_size + IV_SIZE]
    ciphertext = combined[key_size + IV_SIZE :]

    # Load private key
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(private_key, RSAPrivateKey):
        raise TypeError("Expected RSA private key")

    # Decrypt AES key with RSA-OAEP
    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Decrypt invoice XML with AES-256-CBC
    return _decrypt_aes_cbc(ciphertext, aes_key, iv)
