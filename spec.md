# Simple Streaming Serialize

## Types

### Basic Types

- `uint<N>`: `N`-bit unsigned integer where `N % 8 == 0` and `8 <= N <= 256`
- `scalar<N>`: An alternate encoding of `uint<N>` for more compact serialization
- `bit`: 1-bit unsigned integer

### Composite Types

- `container`: fixed length heterogenous collection of values
  - Denoted with curly braces `{type1, type2, ..., typeN}`
  - e.g. `{uint64, bool}`
- `tuple`: fixed length homogenous collection of values
  - Denoted with brackets `[N]` where `N` denotes collection size
  - e.g. `uint64[4]` for a length-4 collection of `uint64` values.
- `array`: dynamic length homogenous collection of values
  - Denoted with brackets `[]`
  - e.g. `uint64[]` for a dynamic length collection of `uint64` values


### Aliases

We define the following aliases which **MUST** be supported.

- `byte -> uint8` 
- `bytes -> byte[]`
- `bytesN -> byte[N]`
- `bool -> bit`

### Optionals

- `<type>?`: Any type can be marked as *optional*


## Serialization

Serialization is defined recursively by the function `serialize` which consumes
a `value` of a specified type and produces a binary byte string.

The following conventions are assumed:

- The variable `N` is used to denote length and is constrained `0 <= N <= 2**32 - 1`
- The variable `bit_size` is used to denote the bitsize of either a `uint` or `scalar` and is constrained by the rules:
  - `bit_size % 8 == 0`: e.g. a multiple of 8
  - `0 <= bit_size <= 256`: e.g. minimum of `8` bits and maximum of `256` bits.
- The hexary notation `0x00` is used to represent individual byte values.
- The notation `x0, x1, ..., xN` is use to denote a fixed-length collection of length `N`
- The notation `x0, x1, ...` is used to denote a dynamic length collection.
- The operator `+` is used to denote concatenation of two binary byte strings.

Additionally, the python code examples use these conventions for variable names:

- The variable `value` is used to denote a singular value
- The variable `values` is used to denote collection of homogenous values
- The variabee `item` is used to denote a single item from a homogenous collection
- The variable `elements` is used to denote collection of heterogenous values
- The variable `element` is used to denote a single element from a heterogenous collection


All examples assume the value being serialized has undergone validation

Lastly, may of the python examples make use of a *magic* function referred to
as `magic_serialize`.  The exact implementation of this function is out of
scope for this spec, but it is defined as returning the proper serialized
representation of the given value. 

> A *real* implementation would require type information to be supplied for individual values since it is not possible to determine the proper serialization for an arbitrarily supplied value.


### Bits: `bit`

- `0x01` if the bit is set.
- `0x00` if the bit is **not** set.


> TODO: Consider specialized `bitfield` alias which can natively be deserialized into a sequence of bits (rather than bytes)


```python
def serialize_bit(value: bool) -> bytes:
    if value:
        return b'\x01'
    else:
        return b'\x00'
```


### Unsigned Integer: `uint<N>`

The integer is converted to a sequence of bytes in little endian byte order.

> Assumes prior validation that `bit_size` is a proper bit-size and `value` fits in the range.


```python
def serialize_uintN(bit_size: int, value: int) -> bytes:
    return value.to_bytes(bit_size, "little")
```


### Scalar Integer: `scalar<N>`

The integer is encoded using [unsigned LEB128](https://en.wikipedia.org/wiki/LEB128#Unsigned_LEB128) encoding with the
following constraints.

- The serialized value **must** be encoded using the smallest number of bytes.  Empty trailing bytes are not allowed.


```python
def serialize_scalar(bit_size: int, value: int) -> bytes:
    LOW_MASK = 0b01111111  # lowermost 7 bits set
    HIGH_MASK = 0b10000000  # highest bit set

    result = bytearray()  # a mutable container for accumulating the serialized bytes

    while True:
        # pull the lowermost 7-bits off the value
        byte = value & LOW_MASK

        # shift the lowermost 7-bits off of the value
        value >>= 7

        if value:
            # set the high bit in since we are not finished serializing
            byte |= HIGH_MASK

        result.append(byte)

        if not value:
            # if we have fully serialized the value, break from the loop
            break
    return bytes(result)
```

### Containers: `{<type0>, <type1>, ..., <typeN>}`

Container types are serialized as the concatenation of each of their serialized elements.

> Note that containers can be nested, making this a recursive operation.

- Let `E` be the container value comprised of the individual elements `[e0, e1, ..., eN]`
- Let `S` be the sequence `[serializer0, serializer1, ..., serializerN]` denoting the individual serialization functions for the elements from `E`

The result is the concatenation of the individual serialized elements computed by applying the serialization functions from `S` to the element values from `E`: e.g.  `serializer0(e0) + serializer1(e1) + ... + serializerN(eN)`


```python
def serialize_container(value):
    return b''.join((
        magic_serialize(element)
        for element in value
    ))
```


### Tuples: `<type>[N]`


Tuples types are serialized as the concatenation of each of the serialized items.

- Let `V` be the tuple value containing the individual elements `[v0, v1, ..., vN]`
- Let `serialize_type` be the serialization function for the value type of `V`

The result is the concatenation of applying `serialize_type` to each value: e.g. `serialize_type(v0) + serialize_type(v1) + ... + serialize_type(vN)`


```python
def serialize_container(values):
    return b''.join((
        magic_serialize(item)
        for item in values
    ))
```


### Arrays: `<type>[]`

Arrays are serialized as the length prefixed concatenation of the individual items.

- Let `V` be the array value containing the individual elements `[v0, v1, ...]`
- Let `L` be the number of elements in `V`
- let `length_prefix` be the result of serializing `L` as a `scalar32`
- Let `serialized_values` be the result of serializing `V` as an equivalent Tuple type of length `L`

The result is the concatenation of `length_prefix` and `serialized_values`: e.g. `length_prefix + serialized_values`
