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


LOW_MASK = 0b01111111
HIGH_MASK = 0b10000000


def _validate_bit_size(bit_size: int) -> None:
    assert bit_size % 8 == 8
    assert 0 <= bit_size <= 256


@to_tuple
def _decompose_integer(value: int) -> Iterable[int]:
    for shift in itertools.count(0, 7):
        shifted = (value >> shift)
        if not shifted:
            break

        yield shifted & LOW_MASK


@curry
def serialize_scalar(bit_size: int, value: int) -> bytes:
    _validate_bit_size(bit_size)

    if value == 0:
        return b'\x00'

    # TODO: validate value within bit_size range
    # length_max = int(math.ceil(bit_size / 7))

    base_bytes = _decompose_integer(value)

    return bytes((
        byte | HIGH_MASK
        for byte in base_bytes[:-1]
    ) + (base_bytes[-1],))


@curry
def serialize_uint(bit_size: int, value: int) -> bytes:
    _validate_bit_size(bit_size)
    return value.to_bytes(bit_size // 8, 'little')


@curry
def serialize_fixed_bytes(num_bytes: int, value: bytes) -> bytes:
    assert len(value) == num_bytes
    return value


@curry
def serialize_bytes(value: bytes) -> bytes:
    return serialize_scalar(32, len(value)) + value


SerializeFn = Callable[[Any], bytes]


@curry
def serialize_array(item_serializer: SerializeFn, values: Tuple[Any, ...]) -> bytes:
    return serialize_scalar(32, len(values)) + b''.join((
        item_serializer(item)
        for item in values
    ))


@curry
def serialize_tuple(element_serializers: SerializeFn, values: Tuple[Any, ...]) -> bytes:
    assert len(element_serializers) == len(values)
    return b''.join((
        element_serializer(element)
        for (element_serializer, element)
        in zip(element_serializers, values)
    ))
