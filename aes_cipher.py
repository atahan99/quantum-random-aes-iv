"""
aes_cipher.py

Provides QuantumAESCipher: an AES-256-CBC cipher whose initialization
vector is supplied externally as a 128-bit binary string — intended to
be sourced from quantum_iv_generator.fetch_quantum_iv().

Design notes:
  - Key derivation: passphrase → SHA-256 → 32-byte key (AES-256)
  - IV:             128-bit quantum bitstring → 16-byte bytearray
  - Padding:        PKCS#7 (manual implementation compatible with PyCryptodome)
  - Output format:  base64(IV ‖ ciphertext)  — IV is prepended so the
                    recipient can extract it without a separate channel.

WARNING: For production systems, replace SHA-256 key derivation with a
proper KDF (Argon2id or PBKDF2-HMAC-SHA256) with a unique salt.
"""

import hashlib
from base64 import b64encode, b64decode
from Crypto.Cipher import AES


BLOCK_BYTES = AES.block_size   # 16 bytes = 128 bits


class QuantumAESCipher:
    """
    AES-256-CBC cipher initialised with a quantum-generated IV.

    Parameters
    ----------
    passphrase : str
        Human-readable secret. Hashed to a 32-byte AES key via SHA-256.
    iv_bitstring : str
        128-character binary string ('0'/'1') produced by the QRNG module.
    """

    def __init__(self, passphrase: str, iv_bitstring: str):
        self.key: bytes = hashlib.sha256(passphrase.encode()).digest()
        self.iv:  bytes = self._bitstring_to_bytes(iv_bitstring)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext and return base64(IV ‖ ciphertext).

        The IV is prepended to the ciphertext so that decryption only
        requires the ciphertext blob and the passphrase.
        """
        padded = self._pkcs7_pad(plaintext)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        ciphertext = cipher.encrypt(padded.encode("utf-8"))
        return b64encode(self.iv + ciphertext).decode("utf-8")

    def decrypt(self, b64_ciphertext: str) -> str:
        """
        Decrypt a base64-encoded blob produced by encrypt().

        Extracts the IV from the first 16 bytes of the decoded blob,
        then decrypts the remainder.
        """
        raw = b64decode(b64_ciphertext)
        extracted_iv = raw[:BLOCK_BYTES]
        ciphertext   = raw[BLOCK_BYTES:]
        cipher = AES.new(self.key, AES.MODE_CBC, extracted_iv)
        padded_plain = cipher.decrypt(ciphertext).decode("utf-8")
        return self._pkcs7_unpad(padded_plain)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _bitstring_to_bytes(bitstring: str) -> bytes:
        """
        Convert a binary string such as '10110...' to a bytes object.

        The string is interpreted as a big-endian unsigned integer, then
        sliced into 8-bit groups to form each byte. The resulting byte
        sequence is returned in most-significant-byte-first order.
        """
        value = int(bitstring, 2)
        byte_list = []
        while value:
            byte_list.append(value & 0xFF)
            value >>= 8
        byte_list.reverse()
        return bytes(byte_list)

    @staticmethod
    def _pkcs7_pad(text: str) -> str:
        """
        Apply PKCS#7 padding so that len(text) becomes a multiple of
        BLOCK_BYTES. The padding character encodes the number of bytes
        added, allowing deterministic removal after decryption.
        """
        pad_len = BLOCK_BYTES - (len(text) % BLOCK_BYTES)
        return text + chr(pad_len) * pad_len

    @staticmethod
    def _pkcs7_unpad(text: str) -> str:
        """Remove PKCS#7 padding added by _pkcs7_pad."""
        pad_len = ord(text[-1])
        return text[:-pad_len]


if __name__ == "__main__":
    # Quick sanity check with a pseudo-random IV (not from QPU)
    import os
    dummy_iv = "".join(format(b, "08b") for b in os.urandom(16))
    cipher = QuantumAESCipher("test-passphrase", dummy_iv)
    ct = cipher.encrypt("Hello, quantum world!")
    pt = cipher.decrypt(ct)
    assert pt == "Hello, quantum world!", "Round-trip failed"
    print("[+] Self-test passed")
    print(f"    Ciphertext: {ct}")
