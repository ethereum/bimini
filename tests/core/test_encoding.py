import pytest

from bimini.types import (
    BitType,
    BoolType,
    ByteType,
    BytesType,
    ScalarType,
    UnsignedIntegerType,
)
from bimini.grammar import parse


@pytest.mark.parametrize(
    'value,expected',
    (
        (True, b'\x01'),
        (False, b'\x00'),
    ),
)
def test_bit_type_encoding(value, expected):
    actual = BitType().encode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (True, b'\x01'),
        (False, b'\x00'),
    ),
)
def test_bool_type_encoding(value, expected):
    actual = BoolType().encode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'bit_size,value,expected',
    (
        (8, 0, b'\x00'),
        (16, 0, b'\x00\x00'),
        (8, 1, b'\x01'),
        (16, 1, b'\x01\x00'),
        (16, 2**16 - 1, b'\xff\xff'),
    ),
)
def test_uint_type_encoding(bit_size, value, expected):
    actual = UnsignedIntegerType(bit_size).encode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'bit_size,value,expected',
    (
        (8, 0, b'\x00'),
        (16, 0, b'\x00'),
        (8, 1, b'\x01'),
        (16, 1, b'\x01'),
        (16, 2**16 - 1, b'\xff\xff\x03'),
    ),
)
def test_scalar_type_encoding(bit_size, value, expected):
    actual = ScalarType(bit_size).encode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'value',
    tuple(bytes((value,)) for value in range(256)),
)
def test_byte_type_encoding(value):
    actual = ByteType().encode(value)
    assert actual == value


@pytest.mark.parametrize(
    'value,expected',
    (
        (b'\x00', b'\x01\x00'),
        (b'\x01', b'\x01\x01'),
        (b'\xff\xff', b'\x02\xff\xff'),
    ),
)
def test_bytes_type_encoding(value, expected):
    actual = BytesType().encode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'type_str,elements,expected',
    (
        ('{byte}', (b'\xab',), b'\xab'),
        ('{byte,uint8}', (b'\xab', 1), b'\xab\x01'),
        ('{byte,uint8[2]}', (b'\xab', (1, 2)), b'\xab\x01\x02'),
        ('{byte,uint8[]}', (b'\xab', (1, 2)), b'\xab\x02\x01\x02'),
    ),
)
def test_container_type_encoding(type_str, elements, expected):
    container_type = parse(type_str)
    actual = container_type.encode(elements)
    assert actual == expected


@pytest.mark.parametrize(
    'type_str,elements,expected',
    (
        ('uint8[3]', (1, 2, 3), b'\x01\x02\x03'),
        ('uint16[3]', (1, 2, 3), b'\x01\x00\x02\x00\x03\x00'),
        ('bool[3]', (True, False, True), b'\x01\x00\x01'),
    ),
)
def test_tuple_type_encoding(type_str, elements, expected):
    container_type = parse(type_str)
    actual = container_type.encode(elements)
    assert actual == expected


@pytest.mark.parametrize(
    'type_str,elements,expected',
    (
        ('uint8[]', (1, 2, 3), b'\x03\x01\x02\x03'),
        ('uint16[]', (1, 2, 3), b'\x03\x01\x00\x02\x00\x03\x00'),
        ('bool[]', (True, False, True), b'\x03\x01\x00\x01'),
    ),
)
def test_array_type_encoding(type_str, elements, expected):
    container_type = parse(type_str)
    actual = container_type.encode(elements)
    assert actual == expected
