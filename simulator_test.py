"""
simulator_test.py

Standalone integration test using the Braket LocalSimulator.
No AWS credentials or internet access required.

Runs a full encrypt → decrypt round-trip and prints intermediate
values so the data flow can be traced visually.
"""

from quantum_iv_generator import fetch_quantum_iv
from aes_cipher import QuantumAESCipher

TEST_MESSAGES = [
    "The quick brown fox jumps over the lazy dog.",
    "AES-CBC with a quantum IV — no PRNG required.",
    "Short.",
    "A" * 64,   # exactly 4 AES blocks of padding boundary test
]

TEST_PASSPHRASE = "simulator-test-passphrase-2026"


def main() -> None:
    print("=" * 60)
    print(" quantum-random-aes-iv  |  Simulator Integration Test")
    print("=" * 60)

    for idx, message in enumerate(TEST_MESSAGES, start=1):
        print(f"\n[Test {idx}]")
        print(f"  Plaintext  : {message[:50]}{'...' if len(message) > 50 else ''}")

        # Generate quantum IV from local simulator
        iv_bits = fetch_quantum_iv(use_simulator=True)
        print(f"  IV bits    : {iv_bits[:32]}... ({len(iv_bits)} bits)")
        print(f"  IV hex     : {int(iv_bits, 2):032x}")

        # Encrypt
        cipher = QuantumAESCipher(TEST_PASSPHRASE, iv_bits)
        ciphertext = cipher.encrypt(message)
        print(f"  Ciphertext : {ciphertext[:60]}...")

        # Decrypt and verify
        recovered = cipher.decrypt(ciphertext)
        status = "PASS" if recovered == message else "FAIL"
        print(f"  Decrypted  : {recovered[:50]}{'...' if len(recovered) > 50 else ''}")
        print(f"  Round-trip : [{status}]")

    print("\n" + "=" * 60)
    print(" All tests complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
