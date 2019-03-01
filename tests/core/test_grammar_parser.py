import pytest

from bimini.types import (
    ArrayType,
    BitType,
    BoolType,
    ByteType,
    BytesType,
    FixedBytesType,
    ContainerType,
    ScalarType,
    OptionalType,
    TupleType,
    UnsignedIntegerType,
)
from bimini.grammar import parse

t_bit = BitType()
t_bool = BoolType()
t_byte = ByteType()
t_bytes = BytesType()
t_bytes32 = FixedBytesType(32)
t_uint8 = UnsignedIntegerType(8)
t_scalar8 = ScalarType(8)
t_uint16 = UnsignedIntegerType(16)
t_scalar16 = ScalarType(16)
t_uint256 = UnsignedIntegerType(256)
t_scalar256 = ScalarType(256)


@pytest.mark.parametrize(
    'type_str,expected',
    (
        ('bit', t_bit),
        ('bool', t_bool),
        ('byte', t_byte),
        ('bytes', t_bytes),
        ('bytes32', t_bytes32),
        ('uint8', t_uint8),
        ('scalar8', t_scalar8),
        ('uint16', t_uint16),
        ('scalar16', t_scalar16),
        # TODO: enumerate
        ('uint256', t_uint256),
        ('scalar256', t_scalar256),
    ),
)
def test_parsing_basic_type_strings(type_str, expected):
    result = parse(type_str)
    assert result == expected


t_uint8_tuple10 = TupleType(t_uint8, 10)

t_uint8_tuple5 = TupleType(t_uint8, 5)

t_uint8_tuple10_tuple5 = TupleType(t_uint8_tuple5, 10)

t_uint8_tuple10_arr = TupleType(ArrayType(t_uint8), 10)

t_uint8_tuple10_tuple5_arr = TupleType(TupleType(ArrayType(t_uint8), 5), 10)

t_uint8_tuple10_arr_tuple5 = TupleType(ArrayType(TupleType(t_uint8, 5)), 10)

t_cont_uint8_scalar8 = ContainerType((t_uint8, t_scalar8))
t_cont_uint8_scalar8_tuple5 = TupleType(t_cont_uint8_scalar8, 5)


@pytest.mark.parametrize(
    'type_str,expected',
    (
        ('uint8[10]', t_uint8_tuple10),
        ('uint8[10][5]', t_uint8_tuple10_tuple5),
        ('uint8[10][]', t_uint8_tuple10_arr),
        ('uint8[10][5][]', t_uint8_tuple10_tuple5_arr),
        ('uint8[10][][5]', t_uint8_tuple10_arr_tuple5),
        # containers
        ('{uint8,scalar8}[5]', t_cont_uint8_scalar8_tuple5),
    ),
)
def test_parsing_tuple_integer_type_strings(type_str, expected):
    result = parse(type_str)
    assert result == expected


@pytest.mark.parametrize(
    'type_str,item_type',
    (
        # TODO: inturn type values
        ('uint8[]', UnsignedIntegerType(8)),
        ('scalar8[]', ScalarType(8)),
        ('uint8[][5]', TupleType(UnsignedIntegerType(8), 5)),
        ('scalar8[][5]', TupleType(ScalarType(8), 5)),
        ('uint8[][]', ArrayType(UnsignedIntegerType(8))),
        ('scalar8[][]', ArrayType(ScalarType(8))),
        ('uint8[][5][]', TupleType(ArrayType(UnsignedIntegerType(8)), 5)),
        ('scalar8[][5][]', TupleType(ArrayType(ScalarType(8)), 5)),
        ('uint8[][][5]', ArrayType(TupleType(UnsignedIntegerType(8), 5))),
        ('scalar8[][][5]', ArrayType(TupleType(ScalarType(8), 5))),
        # containers
        (
            '{uint8,scalar8}[]',
            ContainerType((UnsignedIntegerType(8), ScalarType(8))),
        ),
    ),
)
def test_parsing_array_integer_type_strings(type_str, item_type):
    result = parse(type_str)
    assert isinstance(result, ArrayType)
    assert item_type == result.item_type


t_cont_uint8_cont_uint_16_scalar16 = ContainerType((
    t_uint8,
    ContainerType((t_uint16, t_scalar16)),
))


@pytest.mark.parametrize(
    'type_str,expected',
    (
        ('{uint8}', ContainerType((t_uint8,))),
        ('{uint8,scalar8}', t_cont_uint8_scalar8),
        ('{uint8,{uint16,scalar16}}', t_cont_uint8_cont_uint_16_scalar16),
    ),
)
def test_parsing_container_type_strings(type_str, expected):
    result = parse(type_str)
    assert result == expected


@pytest.mark.parametrize(
    'type_str,expected',
    (
        ('uint8?', OptionalType(t_uint8)),
        ('byte?', OptionalType(t_byte)),
        ('uint8?[]', ArrayType(OptionalType(t_uint8))),
        ('uint8[]?', OptionalType(ArrayType(t_uint8))),
    ),
)
def test_parsing_optional_types(type_str, expected):
    result = parse(type_str)
    assert result == expected
