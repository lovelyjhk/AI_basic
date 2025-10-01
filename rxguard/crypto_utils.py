from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import constant_time
import xxhash


MASTER_KEY_BYTES = 32


def secure_write_file(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    # 0o600 ensures user read/write only on POSIX
    with os.fdopen(os.open(path, flags, 0o600), "wb") as f:
        f.write(data)


def load_or_create_master_key(path: str) -> bytes:
    if os.path.exists(path):
        with open(path, "rb") as f:
            key = f.read()
        if len(key) != MASTER_KEY_BYTES:
            raise ValueError("Invalid master key length")
        return key
    key = os.urandom(MASTER_KEY_BYTES)
    secure_write_file(path, key)
    return key


def compute_chunk_hash(plaintext: bytes) -> str:
    return xxhash.xxh64_hexdigest(plaintext)


def derive_chunk_key_and_nonce(master_key: bytes, chunk_hash_hex: str) -> Tuple[bytes, bytes]:
    info = ("rxguard:chunk:" + chunk_hash_hex).encode("utf-8")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32 + 12,  # 32 bytes key + 12 bytes nonce
        salt=None,
        info=info,
    )
    material = hkdf.derive(master_key)
    return material[:32], material[32:]


def encrypt_chunk(plaintext: bytes, master_key: bytes) -> Tuple[str, bytes]:
    """Encrypt plaintext deterministically given the master key.

    Returns (chunk_hash_hex, ciphertext)

    Security note: deterministic encryption is chosen to enable deduplication.
    This has privacy trade-offs and should be used only in trusted environments.
    """
    chunk_hash_hex = compute_chunk_hash(plaintext)
    key, nonce = derive_chunk_key_and_nonce(master_key, chunk_hash_hex)
    aead = ChaCha20Poly1305(key)
    ciphertext = aead.encrypt(nonce, plaintext, associated_data=chunk_hash_hex.encode("utf-8"))
    return chunk_hash_hex, ciphertext


def decrypt_chunk(chunk_hash_hex: str, ciphertext: bytes, master_key: bytes) -> bytes:
    key, nonce = derive_chunk_key_and_nonce(master_key, chunk_hash_hex)
    aead = ChaCha20Poly1305(key)
    return aead.decrypt(nonce, ciphertext, associated_data=chunk_hash_hex.encode("utf-8"))


def constant_time_compare(a: bytes, b: bytes) -> bool:
    return constant_time.bytes_eq(a, b)

