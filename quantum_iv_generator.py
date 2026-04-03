"""
quantum_iv_generator.py

Generates a 128-bit initialization vector string using a single-qubit
Hadamard circuit executed on an AWS Braket quantum processing unit.

The Hadamard gate places a |0⟩ qubit into equal superposition:
    H|0⟩ = (|0⟩ + |1⟩) / √2

Measuring this state collapses it to either 0 or 1 with exactly 50%
probability each — a source of true quantum randomness. Running the
circuit for 128 independent shots yields 128 uncorrelated random bits,
forming a 16-byte IV suitable for AES-CBC.

Usage:
    from quantum_iv_generator import fetch_quantum_iv
    iv_bitstring = fetch_quantum_iv()   # returns e.g. '10110100...'
"""

import numpy as np
from braket.circuits import Circuit
from braket.aws import AwsDevice
from braket.devices import LocalSimulator

# ---------------------------------------------------------------------------
# AWS Braket configuration
# ---------------------------------------------------------------------------
BRACKET_BUCKET  = "amazon-braket-your-bucket-name"   # Replace with your S3 bucket
BRACKET_PREFIX  = "quantum-iv-results"
S3_DESTINATION  = (BRACKET_BUCKET, BRACKET_PREFIX)

# Rigetti Aspen-M-3 QPU ARN (update to whichever Rigetti device is available)
RIGETTI_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3"

# Number of shots == number of random bits in the IV (AES-CBC needs 128)
IV_BIT_LENGTH = 128


def _build_single_qubit_hadamard() -> Circuit:
    """
    Construct a one-qubit circuit with a single Hadamard gate.

    The circuit contains no entanglement and no two-qubit gates; each
    shot produces one perfectly unbiased classical bit after measurement.
    """
    circuit = Circuit()
    circuit.h(0)          # Apply H to qubit index 0
    return circuit


def fetch_quantum_iv(use_simulator: bool = False) -> str:
    """
    Execute the Hadamard circuit on a QPU (or local simulator) and collect
    IV_BIT_LENGTH measurement outcomes, returning them as a binary string.

    Parameters
    ----------
    use_simulator : bool
        When True, routes to Braket's LocalSimulator instead of the QPU.
        Useful for development and CI pipelines where QPU access is not
        available or cost/latency is prohibitive.

    Returns
    -------
    str
        A string of exactly IV_BIT_LENGTH '0'/'1' characters, e.g.
        '10110010110100101101001011010010...'
    """
    circuit = _build_single_qubit_hadamard()

    if use_simulator:
        device = LocalSimulator()
        task = device.run(circuit, shots=IV_BIT_LENGTH)
    else:
        device = AwsDevice(RIGETTI_ARN)
        task = device.run(circuit, S3_DESTINATION, shots=IV_BIT_LENGTH)

    result = task.result()
    measurements = result.measurements          # shape: (IV_BIT_LENGTH, 1)

    # Flatten each single-qubit measurement into a character and join
    iv_bitstring = "".join(str(measurements[shot][0]) for shot in range(IV_BIT_LENGTH))

    return iv_bitstring


if __name__ == "__main__":
    print("[*] Requesting quantum IV from local simulator...")
    test_iv = fetch_quantum_iv(use_simulator=True)
    print(f"[+] IV bitstring ({len(test_iv)} bits): {test_iv}")
    print(f"[+] IV hex: {int(test_iv, 2):032x}")
