"""Tests for invoice encryption."""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

from ksef.encryption import (
    AES_KEY_SIZE,
    IV_SIZE,
    _decrypt_aes_cbc,
    _encrypt_aes_cbc,
    _encrypt_key_rsa_oaep,
    _load_public_key_from_b64,
    _pad_data,
    _unpad_data,
    decrypt_invoice,
    encrypt_invoice,
)


def _generate_test_keypair() -> tuple[bytes, str]:
    """Generate RSA key pair for testing.

    Returns
    -------
    tuple[bytes, str]
        PEM-encoded private key and base64-encoded DER public key.
    """
    private_key = generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_b64 = base64.b64encode(public_key_der).decode("ascii")

    return private_key_pem, public_key_b64


def test_pad_unpad_roundtrip() -> None:
    """Test PKCS7 padding and unpadding round-trip."""
    data = b"Hello, World!"
    padded = _pad_data(data)
    unpadded = _unpad_data(padded)
    assert unpadded == data


def test_pad_block_aligned() -> None:
    """Test padding when data is already block-aligned."""
    # 16 bytes (one block)
    data = b"0123456789ABCDEF"
    padded = _pad_data(data)
    # PKCS7 adds a full block of padding when aligned
    assert len(padded) == 32  # noqa: PLR2004
    unpadded = _unpad_data(padded)
    assert unpadded == data


def test_aes_cbc_roundtrip() -> None:
    """Test AES-256-CBC encryption and decryption round-trip."""
    key = b"0" * AES_KEY_SIZE  # 32 bytes
    iv = b"1" * IV_SIZE  # 16 bytes
    plaintext = b"This is a test invoice XML content."

    ciphertext = _encrypt_aes_cbc(plaintext, key, iv)
    decrypted = _decrypt_aes_cbc(ciphertext, key, iv)

    assert decrypted == plaintext


def test_aes_cbc_different_keys_produce_different_ciphertext() -> None:
    """Test that different keys produce different ciphertext."""
    key1 = b"A" * AES_KEY_SIZE
    key2 = b"B" * AES_KEY_SIZE
    iv = b"0" * IV_SIZE
    plaintext = b"Test data"

    ciphertext1 = _encrypt_aes_cbc(plaintext, key1, iv)
    ciphertext2 = _encrypt_aes_cbc(plaintext, key2, iv)

    assert ciphertext1 != ciphertext2


def test_rsa_oaep_key_wrapping() -> None:
    """Test RSA-OAEP key wrapping."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    private_key = generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    aes_key = b"K" * AES_KEY_SIZE  # 32 bytes

    encrypted_key = _encrypt_key_rsa_oaep(aes_key, public_key)

    # Decrypt with private key
    decrypted_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    assert decrypted_key == aes_key


def test_load_public_key_from_b64() -> None:
    """Test loading RSA public key from base64-encoded DER."""
    _private_key_pem, public_key_b64 = _generate_test_keypair()

    public_key = _load_public_key_from_b64(public_key_b64)

    assert public_key.key_size == 2048  # noqa: PLR2004


def test_encrypt_invoice_format() -> None:
    """Test that encrypt_invoice produces correctly formatted output."""
    _private_key_pem, public_key_b64 = _generate_test_keypair()

    invoice_xml = b"<?xml version='1.0'?><Faktura>test</Faktura>"

    result = encrypt_invoice(invoice_xml, public_key_b64)

    # Result should be base64-encoded
    decoded = base64.b64decode(result.encrypted_content)

    # Should contain encrypted_key (256 bytes for 2048-bit RSA) + iv (16) + ciphertext
    assert len(decoded) > 256 + 16


def test_encrypt_decrypt_invoice_roundtrip() -> None:
    """Test full invoice encryption and decryption round-trip."""
    private_key_pem, public_key_b64 = _generate_test_keypair()

    invoice_xml = b"<?xml version='1.0' encoding='UTF-8'?><Faktura><Test>content</Test></Faktura>"

    encrypted = encrypt_invoice(invoice_xml, public_key_b64)
    decrypted = decrypt_invoice(encrypted.encrypted_content, private_key_pem)

    assert decrypted == invoice_xml


def test_encrypt_invoice_different_each_time() -> None:
    """Test that encryption produces different output each time (due to random IV and key)."""
    _private_key_pem, public_key_b64 = _generate_test_keypair()

    invoice_xml = b"<Faktura>same content</Faktura>"

    result1 = encrypt_invoice(invoice_xml, public_key_b64)
    result2 = encrypt_invoice(invoice_xml, public_key_b64)

    # Different random key/IV should produce different ciphertext
    assert result1.encrypted_content != result2.encrypted_content


def test_encrypt_large_invoice() -> None:
    """Test encryption of a larger invoice XML."""
    private_key_pem, public_key_b64 = _generate_test_keypair()

    # Create a larger invoice XML (multiple KB)
    large_content = b"<Row>" + b"X" * 10000 + b"</Row>"
    invoice_xml = b"<?xml version='1.0'?><Faktura>" + large_content * 10 + b"</Faktura>"

    encrypted = encrypt_invoice(invoice_xml, public_key_b64)
    decrypted = decrypt_invoice(encrypted.encrypted_content, private_key_pem)

    assert decrypted == invoice_xml
