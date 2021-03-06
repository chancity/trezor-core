import ustruct

from trezor.crypto import base32
from trezor.wire import ProcessError

from apps.common import HARDENED

KIN_CURVE = "ed25519"


def public_key_from_address(address: str) -> bytes:
    """Extracts public key from an address
    Kin address is in format:
    <1-byte version> <32-bytes ed25519 public key> <2-bytes CRC-16 checksum>
    """
    b = base32.decode(address)
    _crc16_checksum_verify(b[:-2], b[-2:])
    return b[1:-2]


def address_from_public_key(pubkey: bytes):
    """Returns the base32-encoded version of public key bytes (G...)"""
    address = bytearray()
    address.append(6 << 3)  # version -> 'G'
    address.extend(pubkey)
    address.extend(_crc16_checksum(bytes(address)))  # checksum

    return base32.encode(address)


def validate_full_path(path: list) -> bool:
    """
    Validates derivation path to equal 44'/2017'/a',
    where `a` is an account index from 0 to 1 000 000.
    """
    if len(path) != 3:
        return False
    if path[0] != 44 | HARDENED:
        return False
    if path[1] != 2017 | HARDENED:
        return False
    if path[2] < HARDENED or path[2] > 1000000 | HARDENED:
        return False
    return True


def _crc16_checksum_verify(data: bytes, checksum: bytes):
    if _crc16_checksum(data) != checksum:
        raise ProcessError("Invalid address checksum")


def _crc16_checksum(data: bytes) -> bytes:
    """Returns the CRC-16 checksum of bytearray bytes

    Ported from Java implementation at: http://introcs.cs.princeton.edu/java/61data/CRC16CCITT.java.html

    Initial value changed to 0x0000 to match Kin configuration.
    """
    crc = 0x0000
    polynomial = 0x1021

    for byte in data:
        for i in range(8):
            bit = (byte >> (7 - i) & 1) == 1
            c15 = (crc >> 15 & 1) == 1
            crc <<= 1
            if c15 ^ bit:
                crc ^= polynomial

    return ustruct.pack("<H", crc & 0xFFFF)
