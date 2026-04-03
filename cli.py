"""
cli.py

Command-line interface for quantum-random-aes-iv.

Examples
--------
# Encrypt using a real QPU (requires AWS credentials + Braket access)
python cli.py --encrypt --message "top secret" --passphrase "my-key"

# Encrypt using the local Braket simulator (no AWS needed)
python cli.py --encrypt --message "top secret" --passphrase "my-key" --sim

# Decrypt a previously encrypted blob
python cli.py --decrypt --ciphertext "<base64 blob>" --passphrase "my-key"
"""

import argparse
import sys
from quantum_iv_generator import fetch_quantum_iv
from aes_cipher import QuantumAESCipher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AES-256-CBC with a quantum-generated initialization vector"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--encrypt", action="store_true", help="Encrypt a plaintext message")
    mode.add_argument("--decrypt", action="store_true", help="Decrypt a base64 ciphertext blob")

    parser.add_argument("--message",    type=str, help="Plaintext to encrypt")
    parser.add_argument("--ciphertext", type=str, help="Base64 ciphertext blob to decrypt")
    parser.add_argument("--passphrase", type=str, required=True, help="Encryption passphrase")
    parser.add_argument(
        "--sim",
        action="store_true",
        default=False,
        help="Use the local Braket simulator instead of the real QPU",
    )
    return parser.parse_args()


def run_encrypt(message: str, passphrase: str, use_sim: bool) -> None:
    print(f"[*] Fetching quantum IV (simulator={'yes' if use_sim else 'no, using QPU'})...")
    iv_bitstring = fetch_quantum_iv(use_simulator=use_sim)
    print(f"[+] Quantum IV ({len(iv_bitstring)} bits): {iv_bitstring}")
    print(f"[+] IV (hex): {int(iv_bitstring, 2):032x}")

    cipher = QuantumAESCipher(passphrase, iv_bitstring)
    ciphertext = cipher.encrypt(message)
    print(f"\n[+] Ciphertext (base64):\n    {ciphertext}")


def run_decrypt(b64_ciphertext: str, passphrase: str) -> None:
    # For decryption the IV is embedded in the ciphertext blob;
    # we still need a valid QuantumAESCipher instance so we supply a
    # placeholder bitstring — the decrypt() method reads the IV from
    # the ciphertext itself.
    placeholder_iv = "0" * 128
    cipher = QuantumAESCipher(passphrase, placeholder_iv)
    plaintext = cipher.decrypt(b64_ciphertext)
    print(f"[+] Decrypted plaintext: {plaintext}")


def main() -> None:
    args = parse_args()

    if args.encrypt:
        if not args.message:
            print("[!] --message is required for --encrypt", file=sys.stderr)
            sys.exit(1)
        run_encrypt(args.message, args.passphrase, args.sim)

    elif args.decrypt:
        if not args.ciphertext:
            print("[!] --ciphertext is required for --decrypt", file=sys.stderr)
            sys.exit(1)
        run_decrypt(args.ciphertext, args.passphrase)


if __name__ == "__main__":
    main()
