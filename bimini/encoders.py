import itertools
from typing import (
    Any,
    Iterable,
    Callable,
    Tuple,
)
from cytoolz import curry

from bimini._utils.decorators import (
    to_tuple,
)

from bimini.exceptions import (
    EncodingError,
)


LOW_MASK = 0b01111111
HIGH_MASK = 0b10000000


def _validate_bit_size(bit_size: int) -> None:
    assert bit_size % 8 == 0
    assert 8 <= bit_size


@to_tuple
def _decompose_integer(value: int) -> Iterable[int]:
    for shift in itertools.count(0, 7):
        shifted = (value >> shift)
        if not shifted:
            break

        yield shifted & LOW_MASK


def encode_bool(value: bool) -> bytes:
    if value is True:
        return b'\x01'
    elif value is False:
        return b'\x00'
    else:
        raise EncodingError("TODO: INVALID")


@curry
def encode_scalar(bit_size: int, value: int) -> bytes:
    _validate_bit_size(bit_size)

    if value == 0:
        return b'\x00'

    # TODO: validate value within bit_size range
    # length_max = int(math.ceil(bit_size / 7))

    base_bytes = _decompose_integer(value)

    return bytes((
        byte | HIGH_MASK
        for byte in base_bytes[:-1]
    )) + bytes(base_bytes[-1:])


@curry
def encode_uint(bit_size: int, value: int) -> bytes:
    _validate_bit_size(bit_size)
    return value.to_bytes(bit_size // 8, 'little')


@curry
def encode_fixed_bytes(num_bytes: int, value: bytes) -> bytes:
    assert len(value) == num_bytes
    return value


@curry
def encode_bytes(value: bytes) -> bytes:
    return encode_scalar(32, len(value)) + value


SerializeFn = Callable[[Any], bytes]


@curry
def encode_container(element_encoders: SerializeFn, elements: Tuple[Any, ...]) -> bytes:
    assert len(element_encoders) == len(elements)
    return b''.join((
        element_encoder(element)
        for (element_encoder, element)
        in zip(element_encoders, elements)
    ))


@curry
def encode_tuple(item_encoder: SerializeFn, values: Tuple[Any, ...]) -> bytes:
    return b''.join((
        item_encoder(item)
        for item
        in values
    ))


@curry
def encode_array(item_encoder: SerializeFn, values: Tuple[Any, ...]) -> bytes:
    return encode_scalar(32, len(values)) + encode_tuple(item_encoder, values)
