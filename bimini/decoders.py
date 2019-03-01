import io
from bimini.exceptions import (
    DecodingError,
)


# TODO: dedup
LOW_MASK = 2**7 - 1
HIGH_MASK = 2**7


def decode_bool(data: bytes) -> bool:
    if data == b'\x01':
        return True
    elif data == b'\x00':
        return False
    else:
        raise DecodingError("TODO: INVALID")


def decode_uint(bit_size: int, data: bytes) -> bool:
    # TODO: validate data length and bitsize
    return int.from_bytes(data, 'little')


def decode_scalar(bit_size: int, data: bytes) -> int:

    max_length = (bit_size + 6) // 7
    if len(data) > max_length:
        raise Exception("Value encoded with empty bytes")

    if data[-1] & HIGH_MASK:
        raise DecodingError("Last bit should not have high bit set")

    head_components = tuple(
        (byte & LOW_MASK) << (shift * 7)
        for shift, byte
        in enumerate(data[:-1])
    )
    tail_component = (data[-1] & LOW_MASK) << ((len(data) - 1) * 7)
    return sum(head_components) + tail_component


def decode_bytes(data: bytes) -> bytes:
    from .parsers import parse_scalar
    stream = io.BytesIO(data)
    length = parse_scalar(32, stream)
    if stream.tell() + length != len(data):
        raise DecodingError("INVALID LENGTH")
    return data[-length:]
