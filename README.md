# quantum-random-aes-iv

AES-256-CBC encryption using quantum-generated initialization vectors sourced from AWS Braket quantum processing units.

## Overview

Classical pseudorandom number generators (PRNGs) derive their output from deterministic algorithms seeded with entropy from the operating system. While adequate for most applications, the predictability of this process is a foundational weakness when IV reuse or seed compromise is part of the threat model.

This project replaces the classical IV source with a single-qubit Hadamard circuit executed on a real QPU. Each qubit measurement collapses from superposition into a 0 or 1 with exactly 50% probability — not probabilistic in the PRNG sense, but non-deterministic at the physical level. Running 128 independent shots yields 128 uncorrelated bits suitable for use as an AES-CBC IV.

## Repository Structure

```
quantum-random-aes-iv/
├── quantum_iv_generator.py   # Hadamard circuit + Braket QPU/simulator interface
├── aes_cipher.py             # AES-256-CBC cipher with quantum IV support
├── cli.py                    # argparse CLI (encrypt / decrypt / --sim flag)
├── simulator_test.py         # Round-trip integration tests (no AWS creds needed)
└── requirements.txt          # Python dependencies
```

## Requirements

- Python 3.10+
- AWS account with Braket access (for real QPU runs)
- S3 bucket for Braket result storage

```bash
pip install -r requirements.txt
```

## Configuration

Before using the QPU path, set your S3 bucket in `quantum_iv_generator.py`:

```python
BRACKET_BUCKET = "amazon-braket-your-bucket-name"   # replace with your bucket
```

AWS credentials must be configured via `~/.aws/credentials` or environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`).

## Usage

### Encrypt

```bash
# Using the local simulator (no AWS credentials needed)
python cli.py --encrypt --message "top secret" --passphrase "my-passphrase" --sim

# Using a real QPU
python cli.py --encrypt --message "top secret" --passphrase "my-passphrase"
```

### Decrypt

```bash
python cli.py --decrypt --ciphertext "<base64 blob>" --passphrase "my-passphrase"
```

### Run integration tests (simulator, no AWS needed)

```bash
python simulator_test.py
```

## How It Works

### Quantum IV Generation

A single-qubit Hadamard circuit is submitted to AWS Braket for 128 shots:

```
|0⟩ ──H── M
```

The Hadamard gate produces the state `(|0⟩ + |1⟩) / √2`. Each measurement yields one unbiased random bit. The 128 outcomes are concatenated into a binary string and converted to 16 bytes.

### Encryption Flow

```
passphrase ──SHA-256──► 32-byte AES key
QPU output ──────────► 16-byte IV
                              │
plaintext ──PKCS#7 pad──► AES-256-CBC ──► base64(IV ‖ ciphertext)
```

The IV is prepended to the ciphertext before base64 encoding, making the blob self-contained for decryption.

## Security Notes

- **Key derivation**: The current implementation uses SHA-256 on the passphrase directly. For production use, replace with Argon2id or PBKDF2-HMAC-SHA256 with a unique per-message salt.
- **Simulator mode**: `LocalSimulator` uses a classical PRNG internally — quantum entropy is only present when running on a real QPU.
- **IV uniqueness**: Each encryption call fetches a fresh IV from the QPU. Never reuse IVs across messages encrypted with the same key.
- **QPU availability**: Real QPU runs incur AWS Braket costs and queue latency. The `--sim` flag is provided for development and testing.

## Sources

- [Amazon Braket Python SDK](https://github.com/amazon-braket/amazon-braket-sdk-python) — QPU circuit execution and LocalSimulator
- [Amazon Braket Developer Guide](https://docs.aws.amazon.com/braket/latest/developerguide/what-is-braket.html) — Device ARNs, S3 result storage, shot semantics
- [PyCryptodome documentation](https://pycryptodome.readthedocs.io/) — AES-CBC, PKCS#7 padding
- [NIST SP 800-38A](https://csrc.nist.gov/publications/detail/sp/800-38a/final) — Recommendation for block cipher modes of operation (CBC)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) — IV requirements and key derivation guidance
