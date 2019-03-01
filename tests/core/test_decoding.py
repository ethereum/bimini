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
        (b'\x01', True),
        (b'\x00', False),
    ),
)
def test_bit_type_decoding(value, expected):
    actual = BitType().decode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'value,expected',
    (
        (b'\x01', True),
        (b'\x00', False),
    ),
)
def test_bool_type_decoding(value, expected):
    actual = BoolType().decode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'bit_size,value,expected',
    (
        (8, b'\x00', 0),
        (16, b'\x00\x00', 0),
        (8, b'\x01', 1),
        (16, b'\x01\x00', 1),
        (16, b'\xff\xff', 2**16 - 1),
    ),
)
def test_uint_type_decoding(bit_size, value, expected):
    actual = UnsignedIntegerType(bit_size).decode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'bit_size,value,expected',
    (
        (8, b'\x00', 0),
        (16, b'\x00', 0),
        (8, b'\x01', 1),
        (16, b'\x01', 1),
        (16, b'\xff\xff\x03', 2**16 - 1),
    ),
)
def test_scalar_type_decoding(bit_size, value, expected):
    actual = ScalarType(bit_size).decode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'value',
    tuple(bytes((value,)) for value in range(256)),
)
def test_byte_type_decoding(value):
    actual = ByteType().decode(value)
    assert actual == value


@pytest.mark.parametrize(
    'value,expected',
    (
        (b'\x01\x00', b'\x00'),
        (b'\x01\x01', b'\x01'),
        (b'\x02\xff\xff', b'\xff\xff'),
    ),
)
def test_bytes_type_decoding(value, expected):
    actual = BytesType().decode(value)
    assert actual == expected


@pytest.mark.parametrize(
    'type_str,elements,expected',
    (
        ('{byte}', b'\xab', (b'\xab',)),
        ('{byte,uint8}', b'\xab\x01', (b'\xab', 1)),
        ('{byte,uint8[2]}', b'\xab\x01\x02', (b'\xab', (1, 2))),
        ('{byte,uint8[]}', b'\xab\x02\x01\x02', (b'\xab', (1, 2))),
    ),
)
def test_container_type_decoding(type_str, elements, expected):
    container_type = parse(type_str)
    actual = container_type.decode(elements)
    assert actual == expected


@pytest.mark.parametrize(
    'type_str,elements,expected',
    (
        ('uint8[3]', b'\x01\x02\x03', (1, 2, 3)),
        ('uint16[3]', b'\x01\x00\x02\x00\x03\x00', (1, 2, 3)),
        ('bool[3]', b'\x01\x00\x01', (True, False, True)),
    ),
)
def test_tuple_type_decoding(type_str, elements, expected):
    container_type = parse(type_str)
    actual = container_type.decode(elements)
    assert actual == expected


@pytest.mark.parametrize(
    'type_str,elements,expected',
    (
        ('uint8[]', b'\x03\x01\x02\x03', (1, 2, 3)),
        ('uint16[]', b'\x03\x01\x00\x02\x00\x03\x00', (1, 2, 3)),
        ('bool[]', b'\x03\x01\x00\x01', (True, False, True)),
    ),
)
def test_array_type_decoding(type_str, elements, expected):
    container_type = parse(type_str)
    actual = container_type.decode(elements)
    assert actual == expected
