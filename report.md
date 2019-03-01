# Ethereum Wire Serialization

## Abstract

This document outlines the needs for data serialization in the context of
serializing objects for network transport and makes a case for adopting a new
serialization format.

# Motivation

The Ethereum network has used RLP for both network transport and object
hashing.  RLP is a custom serialization format that was designed alongside the
various Ethereum protocols.

While RLP has done well, there is room for improvement, specifically at the
networking layer.  

# Analysis


## Evaluation Criteria

The following properties are needed in whatever serialization format is used
for network transport.


### Language Support

Implementations available across different languages, primarily

- Go: go-ethereum
- Rust: Parity
- Python: Trinity & Eth2.0 Research
- Java: Enterprise


### Strongly Typed

Values must be strongly typed.

### Compact / Efficient

The serialized data structures should have minimal overhead when serialized.
The resulting serialized byte-size should be as close to the raw number of
bytes needed to represent the data.


### Streamable

The process of encoding and decoding should support streaming.  Efficient
implementations should be able to encode or decode using `O(1)` memory space.


### Data Types

We require the following data types to be well supported in the format.

- Booleans
- Unsigned integers up to 256 bits.
  - e.g. `transaction.value`
- Fixed length byte strings
  - e.g. `header.parent_hash`
  - not strictly required but effects compactness and requires client-side validation of lengths
- Dynamic length byte strings
  - e.g. `log.data`
- Dynamic length arrays of homogenous types
  - e.g. `block.transactions`
- Fixed length arrays of homogenous types
  - e.g. Discovery protocol `Neighbors` response.
  - not strictly required but effects compactness and requires client-side validation of lengths
- Struct-likes for fixed length collections of heterogenous types.
  - e.g. Blocks, Transactions, Headers, etc.


## Candidates

### Popular Formats

The following formats were not considered.

- JSON
  - Not space efficient
  - No native support for schemas


Ideally, we would make use of a well established binary serialization format
with mature libraries in multiple languages.  The following were evaluated and
dismissed due to the listed reasons.

- Protobuf
  - No support for integers above 64 bits
  - No support for fixed size byte strings
  - No support for fixed size arrays
- Message Pack
  - No support for integers above 64 bits
  - No support for fixed size byte strings
  - No support for fixed size arrays
- CBOR
  - No support for strongly typed integers above 64 bits (supports arbitrary bignums)
  - No support for fixed size byte strings
  - No support for fixed size arrays
  - Serialization format contains extraneous metadata not needed by our protocol


### Custom Formats

Having dismissed popular established formats, the following *custom* formats
were evaluated.


- RLP aka Recursive Length Prefix: 
  - https://github.com/ethereum/wiki/wiki/RLP
  - the established serialization used across most parts of the Ethereum protocols
- SSZ aka Simple Serialize:
  - https://github.com/ethereum/eth2.0-specs/blob/bed888810d5c99cd114adc9907c16268a2a285a9/specs/simple-serialize.md
  - the current serialization scheme being used in Eth2.0
- SSS aka Streamable Simple Serialize (working title):
  - https://github.com/ethereum/bimini/blob/master/spec.md
  - an experimental serialization scheme developed specifically for the networking needs of the Ethereum protocol.


#### RLP

RLP is well known and widely used.

- **Language Support**
  - Strong: Established RLP libraries available across most languages
- **Strongly Typed**
  - No: however strong typing is added at the implementation level for most RLP libraries.
- **Compact / Efficient**
  - Medium:
    - No native support for fixed length byte strings results in extra bytes for length prefix
    - No native support for fixed length arrays results in extra bytes for length prefix
    - No layer-2 support for compact integer serialization
- **Streamable**
  - Yes


#### SSZ

SSZ was created as part of the Eth2.0 research.  It was designed to be simple
and low overhead.

- **Language Support**
  - Low: SSZ implementations are being created as part of the Eth2.0 efforts.  None are well established.
- **Strongly Typed**
  - Yes
- **Compact / Efficient**
  - Poor:
    - No support for compact integer serialization
    - Length prefixes are 32-bit, typically resulting in multiple superflous empty bytes
    - Containers are size prefixed with 32-bit values, all of which are superflous
    - No support for compact integer serialization
- **Streamable**
  - No:
    - Size prefixing container types prevents streaming


#### SSS

SSS was created to specifically address the Ethereum network needs.

- **Language Support**
  - Bad: Only one experimental implementation in python https://github.com/ethereum/bimini
- **Strongly Typed**
  - Yes
- **Compact / Efficient**
  - High
    - Near zero superfluous bytes for most schemas
- **Streamable**
  - Yes


## Side-by-Side Comparison

Empirical tests were done to shows how SSS performs with respect to RLP and SSZ for
the following data structures with respect to their serialized sizes.

- Blocks
- Headers
- Transactions
- Receipts
- Logs
- Accounts
- State Trie Nodes (of depths 0-9)
- Discovery Ping
- Discovery Pong
- Discovery FindNode
- Discovery Neighbours

In every case, SSS serialization resulted in a smaller serialized
representation than it's counterparts in either RLP or SSZ.

The comparison to SSZ is less relevant to the Eth1.0 network, but tests are
planned against the Eth2.0 data structures.


### SSS vs RLP Summary

The comparison to RLP shows that there are multiple places where SSS could
reduce the amount of bandwidth used by Ethereum clients.

- ~3% reduction in block size
- ~50% reduction in receipt size
- ~5% reduction in account size (state sync)
- ~2% reduction in trie-node size

Specific to the discovery protocol:

- ~8% reduction for ping
- ~4% reduction for pong
- ~4% reduction for find-nodes
- ~4% reduction for neighbors

## Conclusion


Streamable Simple Serialize (SSS) seems like a strong candidate for the wire
serialization format used by ethereum clients.

- It is simple and easy to implement (the python implementation took a few days to hit a reasonably well polished MVP)
- An optimized implementation should have similar performance to RLP and better than SSZ
- It is highly compact
- It has native support for all desired data types

It is worth noting that SSS is very similar to SSZ, but it is likely wrong to
try and combine the two.  SSS is optimized for network transport, and thus, it
sacrifices the ability to quickly index into data structures *without decoding
them* for compactness.  The data structures we use for hashing needs to support
this feature which seems to be at odds with compactness, requiring additional
metadata to be enbedded into the data structure to account for dynamically
sized fields.  Thus, we will likely want two serialization formats.  One for
network transport.  One for hashing.


# Raw Test Data

The data for these tests was all sourced from live data on the ethereum mainnet.

- Blocks/Headers/Transactions/Receipts/Logs
  - Sourced from 1000 recent blocks
- Accounts
  - 1000 randomly chosen accounts
- State Trie Nodes
  - Recent state trie from mainnet
- Discovery
  - Messages from live DevP2P network

```
headers      : 1000
blocks       : 1000
receipts     : 88842
txns         : 88842
uncles       : 69
logs         : 91615
accounts     : 1000
trie-depth-0 : 1
trie-depth-1 : 16
trie-depth-2 : 100
trie-depth-3 : 100
trie-depth-4 : 100
trie-depth-5 : 100
trie-depth-6 : 310
trie-depth-7 : 337
trie-depth-8 : 64
trie-depth-9 : 6
ping         : 514
pong         : 784
find-node    : 5
neighbors    : 126
```

### Interpreting the numbers

For each data type the following values were measured:

- average gain:
  - The naive average gain in space efficiency across the data set.
- Percentiles (99th/95th/90th/75th/50th)
  - The Nth percentile representing N% of the data set showed gains of this amount.


### All Comparisons

This table shows the comparison between SSS and RLP/SSZ for serialized sizes.


| TYPE   | OBJ          | AVG DELTA   | DELTA-99th   | DELTA-95th   | DELTA-90th   | DELTA-75th   | DELTA-50th   |
|--------|--------------|-------------|--------------|--------------|--------------|--------------|--------------|
| rlp    | block        | 3.27%       | 0.88%        | 1.59%        | 2.21%        | 3.06%        | 3.47%        |
| rlp    | header       | 2.30%       | 2.22%        | 2.24%        | 2.24%        | 2.24%        | 2.27%        |
| rlp    | receipt      | 50.30%      | -5.18%       | -4.46%       | -3.52%       | 0.47%        | 97.01%       |
| rlp    | log          | 4.26%       | 1.47%        | 2.14%        | 3.23%        | 4.46%        | 4.46%        |
| rlp    | txn          | 4.02%       | 0.97%        | 2.17%        | 2.94%        | 3.51%        | 4.05%        |
| rlp    | acct         | 5.56%       | 5.13%        | 5.13%        | 5.19%        | 5.19%        | 5.71%        |
| rlp    | mini-acct    | 12.53%      | 2.60%        | 2.86%        | 2.86%        | 8.33%        | 9.09%        |
| rlp    | trie-depth-0 | 0.38%       | 0.38%        | 0.38%        | 0.38%        | 0.38%        | 0.38%        |
| rlp    | trie-depth-1 | 0.38%       | 0.38%        | 0.38%        | 0.38%        | 0.38%        | 0.38%        |
| rlp    | trie-depth-2 | 0.38%       | 0.38%        | 0.38%        | 0.38%        | 0.38%        | 0.38%        |
| rlp    | trie-depth-3 | 0.38%       | 0.38%        | 0.38%        | 0.38%        | 0.38%        | 0.38%        |
| rlp    | trie-depth-4 | 0.38%       | 0.38%        | 0.38%        | 0.38%        | 0.38%        | 0.38%        |
| rlp    | trie-depth-5 | 0.39%       | 0.38%        | 0.38%        | 0.38%        | 0.38%        | 0.38%        |
| rlp    | trie-depth-6 | 1.52%       | 0.47%        | 0.56%        | 0.68%        | 1.20%        | 1.79%        |
| rlp    | trie-depth-7 | 1.77%       | 0.99%        | 1.20%        | 1.79%        | 1.80%        | 1.92%        |
| rlp    | trie-depth-8 | 1.84%       | 1.20%        | 1.79%        | 1.80%        | 1.80%        | 1.85%        |
| rlp    | trie-depth-9 | 1.84%       | 1.82%        | 1.82%        | 1.82%        | 1.82%        | 1.82%        |
| rlp    | ping         | 8.76%       | 7.32%        | 7.32%        | 7.32%        | 7.32%        | 7.32%        |
| rlp    | pong         | 3.92%       | 3.92%        | 3.92%        | 3.92%        | 3.92%        | 3.92%        |
| rlp    | find-node    | 4.11%       | 4.11%        | 4.11%        | 4.11%        | 4.11%        | 4.11%        |
| rlp    | neighbors    | 4.81%       | 4.25%        | 4.28%        | 4.28%        | 4.28%        | 4.79%        |
| ssz    | block        | 44.99%      | 18.37%       | 26.18%       | 33.59%       | 43.30%       | 47.40%       |
| ssz    | header       | 22.70%      | 22.27%       | 22.49%       | 22.49%       | 22.52%       | 22.72%       |
| ssz    | receipt      | 54.33%      | 3.44%        | 4.09%        | 4.95%        | 7.96%        | 97.34%       |
| ssz    | log          | 8.46%       | 2.52%        | 4.45%        | 7.14%        | 8.54%        | 8.54%        |
| ssz    | txn          | 52.32%      | 16.85%       | 32.45%       | 47.84%       | 48.77%       | 57.03%       |
| ssz    | acct         | 47.81%      | 43.94%       | 43.94%       | 44.70%       | 44.70%       | 50.00%       |
| ssz    | mini-acct    | 83.68%      | 51.43%       | 51.43%       | 51.43%       | 85.53%       | 86.84%       |
| ssz    | trie-depth-0 | 9.25%       | 9.25%        | 9.25%        | 9.25%        | 9.25%        | 9.25%        |
| ssz    | trie-depth-1 | 9.25%       | 9.25%        | 9.25%        | 9.25%        | 9.25%        | 9.25%        |
| ssz    | trie-depth-2 | 9.25%       | 9.25%        | 9.25%        | 9.25%        | 9.25%        | 9.25%        |
| ssz    | trie-depth-3 | 9.25%       | 9.25%        | 9.25%        | 9.25%        | 9.25%        | 9.25%        |
| ssz    | trie-depth-4 | 9.25%       | 9.25%        | 9.25%        | 9.25%        | 9.25%        | 9.25%        |
| ssz    | trie-depth-5 | 9.60%       | 9.25%        | 9.25%        | 9.25%        | 9.25%        | 9.25%        |
| ssz    | trie-depth-6 | 15.27%      | 7.50%        | 7.56%        | 7.56%        | 7.64%        | 8.04%        |
| ssz    | trie-depth-7 | 10.83%      | 7.56%        | 7.63%        | 7.63%        | 7.63%        | 8.11%        |
| ssz    | trie-depth-8 | 9.37%       | 7.56%        | 7.63%        | 7.63%        | 7.63%        | 8.11%        |
| ssz    | trie-depth-9 | 7.78%       | 7.69%        | 7.69%        | 7.69%        | 7.69%        | 7.69%        |
| ssz    | ping         | 85.65%      | 83.62%       | 83.62%       | 83.62%       | 83.62%       | 83.62%       |
| ssz    | pong         | 66.89%      | 66.89%       | 66.89%       | 66.89%       | 66.89%       | 66.89%       |
| ssz    | find-node    | 32.69%      | 32.69%       | 32.69%       | 32.69%       | 32.69%       | 32.69%       |
| ssz    | neighbors    | 48.93%      | 48.03%       | 48.08%       | 48.08%       | 48.08%       | 48.99%       |


### Data Type Size Information

This table shows information about the relative serialized sizes of each data type.


| TYPE         | OBJ   |   AVG SIZE |   SIZE-99th |   SIZE-95th |   SIZE-90th |   SIZE-75th |   SIZE-50th |
|--------------|-------|------------|-------------|-------------|-------------|-------------|-------------|
| acct         | rlp   |        106 |         112 |         112 |         111 |         111 |         104 |
| acct         | sss   |         68 |          74 |          74 |          73 |          73 |          66 |
| acct         | ssz   |        132 |         132 |         132 |         132 |         132 |         132 |
| block        | rlp   |      16723 |       37848 |       33268 |       30100 |       24945 |       16792 |
| block        | sss   |      16190 |       36818 |       32091 |       29165 |       24198 |       16400 |
| block        | ssz   |      30032 |       73160 |       62489 |       55693 |       44189 |       28331 |
| find-node    | rlp   |         73 |          73 |          73 |          73 |          73 |          73 |
| find-node    | sss   |         70 |          70 |          70 |          70 |          70 |          70 |
| find-node    | ssz   |        104 |         104 |         104 |         104 |         104 |         104 |
| header       | rlp   |        530 |         543 |         536 |         536 |         535 |         531 |
| header       | sss   |        518 |         531 |         524 |         524 |         523 |         519 |
| header       | ssz   |        670 |         683 |         676 |         676 |         675 |         671 |
| log          | rlp   |        168 |         509 |         284 |         187 |         157 |         157 |
| log          | sss   |        161 |         503 |         279 |         182 |         150 |         150 |
| log          | ssz   |        175 |         516 |         292 |         196 |         164 |         164 |
| mini-acct    | rlp   |         18 |          70 |          70 |          70 |          12 |          11 |
| mini-acct    | sss   |         17 |          68 |          68 |          68 |          11 |          10 |
| mini-acct    | ssz   |         86 |         140 |         140 |         140 |          76 |          76 |
| neighbors    | rlp   |        642 |        1018 |         959 |         959 |         959 |         643 |
| neighbors    | sss   |        613 |         975 |         918 |         918 |         918 |         612 |
| neighbors    | ssz   |       1192 |        1876 |        1768 |        1768 |        1768 |        1192 |
| ping         | rlp   |         35 |          41 |          41 |          41 |          41 |          41 |
| ping         | sss   |         32 |          38 |          38 |          38 |          38 |          38 |
| ping         | ssz   |        226 |         232 |         232 |         232 |         232 |         232 |
| pong         | rlp   |         51 |          51 |          51 |          51 |          51 |          51 |
| pong         | sss   |         49 |          49 |          49 |          49 |          49 |          49 |
| pong         | ssz   |        148 |         148 |         148 |         148 |         148 |         148 |
| receipt      | rlp   |        441 |        1901 |         649 |         490 |         426 |         268 |
| receipt      | sss   |        303 |        1873 |         661 |         479 |         432 |           8 |
| receipt      | ssz   |        481 |        1973 |         693 |         529 |         465 |         301 |
| trie-depth-0 | rlp   |        532 |         532 |         532 |         532 |         532 |         532 |
| trie-depth-0 | sss   |        530 |         530 |         530 |         530 |         530 |         530 |
| trie-depth-0 | ssz   |        584 |         584 |         584 |         584 |         584 |         584 |
| trie-depth-1 | rlp   |        532 |         532 |         532 |         532 |         532 |         532 |
| trie-depth-1 | sss   |        530 |         530 |         530 |         530 |         530 |         530 |
| trie-depth-1 | ssz   |        584 |         584 |         584 |         584 |         584 |         584 |
| trie-depth-2 | rlp   |        532 |         532 |         532 |         532 |         532 |         532 |
| trie-depth-2 | sss   |        530 |         530 |         530 |         530 |         530 |         530 |
| trie-depth-2 | ssz   |        584 |         584 |         584 |         584 |         584 |         584 |
| trie-depth-3 | rlp   |        532 |         532 |         532 |         532 |         532 |         532 |
| trie-depth-3 | sss   |        530 |         530 |         530 |         530 |         530 |         530 |
| trie-depth-3 | ssz   |        584 |         584 |         584 |         584 |         584 |         584 |
| trie-depth-4 | rlp   |        532 |         532 |         532 |         532 |         532 |         532 |
| trie-depth-4 | sss   |        530 |         530 |         530 |         530 |         530 |         530 |
| trie-depth-4 | ssz   |        584 |         584 |         584 |         584 |         584 |         584 |
| trie-depth-5 | rlp   |        511 |         532 |         532 |         532 |         532 |         532 |
| trie-depth-5 | sss   |        509 |         530 |         530 |         530 |         530 |         530 |
| trie-depth-5 | ssz   |        563 |         584 |         584 |         584 |         584 |         584 |
| trie-depth-6 | rlp   |        113 |         211 |         179 |         147 |         113 |         107 |
| trie-depth-6 | sss   |        112 |         210 |         178 |         146 |         111 |         105 |
| trie-depth-6 | ssz   |        135 |         264 |         232 |         200 |         136 |         118 |
| trie-depth-7 | rlp   |        104 |         112 |         111 |         111 |         111 |         104 |
| trie-depth-7 | sss   |        102 |         110 |         109 |         109 |         109 |         102 |
| trie-depth-7 | ssz   |        115 |         136 |         136 |         119 |         118 |         111 |
| trie-depth-8 | rlp   |        106 |         112 |         111 |         111 |         111 |         104 |
| trie-depth-8 | sss   |        104 |         110 |         109 |         109 |         109 |         102 |
| trie-depth-8 | ssz   |        115 |         136 |         119 |         118 |         118 |         115 |
| trie-depth-9 | rlp   |        108 |         110 |         110 |         110 |         110 |         110 |
| trie-depth-9 | sss   |        106 |         108 |         108 |         108 |         108 |         108 |
| trie-depth-9 | ssz   |        115 |         117 |         117 |         117 |         117 |         117 |
| txn          | rlp   |        181 |         784 |         333 |         175 |         173 |         119 |
| txn          | sss   |        175 |         775 |         326 |         169 |         166 |         113 |
| txn          | ssz   |        329 |         932 |         484 |         324 |         324 |         270 |



### Blocks

- SSS vs RLP:
  - average: 3.27%
  - 99th   : 0.88%
  - 95th   : 1.59%
  - 90th   : 2.21%
  - 75th   : 3.06%
  - 50th   : 3.47%
- SSS vs SSZ:
  - average: 44.99%
  - 99th   : 18.37%
  - 95th   : 26.18%
  - 90th   : 33.59%
  - 75th   : 43.30%
  - 50th   : 47.40%


### Headers

- SSS vs RLP:
  - average: 2.30%
  - 99th   : 2.22%
  - 95th   : 2.24%
  - 90th   : 2.24%
  - 75th   : 2.24%
  - 50th   : 2.27%
- SSS vs SSZ:
  - average: 22.70%
  - 99th   : 22.27%
  - 95th   : 22.49%
  - 90th   : 22.49%
  - 75th   : 22.52%
  - 50th   : 22.72%


### Transactions

- SSS vs RLP:
  - average: 4.02%
  - 99th   : 0.97%
  - 95th   : 2.17%
  - 90th   : 2.94%
  - 75th   : 3.51%
  - 50th   : 4.05%
- SSS vs SSZ:
  - average: 52.32%
  - 99th   : 16.85%
  - 95th   : 32.45%
  - 90th   : 47.84%
  - 75th   : 48.77%
  - 50th   : 57.03%


### Receipts

Receipts were benchmarked using two different SSS schemas.

- one which uses the `scalar2048` type for the `bloom` field
  - Drastic reduction in size for light or empty bloom filters.
  - Slightly larger serialization for dense bloom filters
- one which uses the `uint2048` type for the `bloom` field
  - Equivalent to current Receipt schema

- SSS with `scalar2048` vs RLP:
  - average: 50.30%
  - 99th   : -5.18%
  - 95th   : -4.46%
  - 90th   : -3.52%
  - 75th   : 0.47%
  - 50th   : 97.01%
- SSS with `scalar2048` vs SSZ:
  - average: 54.33%
  - 99th   : 3.44%
  - 95th   : 4.09%
  - 90th   : 4.95%
  - 75th   : 7.96%
  - 50th   : 97.34%

- SSS with `uint2048` vs RLP:
  - average: 2.57%
  - 99th   : 1.87%
  - 95th   : 1.87%
  - 90th   : 1.87%
  - 75th   : 1.87%
  - 50th   : 2.24%
- SSS with `uint2048` vs SSZ:
  - average: 11.86%
  - 99th   : 6.80%
  - 95th   : 9.49%
  - 90th   : 10.66%
  - 75th   : 11.18%
  - 50th   : 12.62%

### Logs

- SSS vs RLP:
  - average: 4.26%
  - 99th   : 1.47%
  - 95th   : 2.14%
  - 90th   : 3.23%
  - 75th   : 4.46%
  - 50th   : 4.46%
- SSS vs SSZ:
  - average: 8.46%
  - 99th   : 2.52%
  - 95th   : 4.45%
  - 90th   : 7.14%
  - 75th   : 8.54%
  - 50th   : 8.54%


### Accounts

- SSS vs RLP:
  - average: 5.56%
  - 99th   : 5.13%
  - 95th   : 5.13%
  - 90th   : 5.19%
  - 75th   : 5.19%
  - 50th   : 5.71%
- SSS vs SSZ:
  - average: 47.81%
  - 99th   : 43.94%
  - 95th   : 43.94%
  - 90th   : 44.70%
  - 75th   : 44.70%
  - 50th   : 50.00%


### State Trie Nodes (of depths 0-9)

- SSS vs RLP:
- depth 0-4
  - average: 0.38%
  - 99th   : 0.38%
  - 95th   : 0.38%
  - 90th   : 0.38%
  - 75th   : 0.38%
  - 50th   : 0.38%
- depth 5
  - average: 0.39%
  - 99th   : 0.38%
  - 95th   : 0.38%
  - 90th   : 0.38%
  - 75th   : 0.38%
  - 50th   : 0.38%
- depth 6
  - average: 1.52%
  - 99th   : 0.47%
  - 95th   : 0.56%
  - 90th   : 0.68%
  - 75th   : 1.20%
  - 50th   : 1.79%
- depth 7
  - average: 1.77%
  - 99th   : 0.99%
  - 95th   : 1.20%
  - 90th   : 1.79%
  - 75th   : 1.80%
  - 50th   : 1.92%
- depth 8
  - average: 1.84%
  - 99th   : 1.20%
  - 95th   : 1.79%
  - 90th   : 1.80%
  - 75th   : 1.80%
  - 50th   : 1.85%
- depth 9
  - average: 1.84%
  - 99th   : 1.82%
  - 95th   : 1.82%
  - 90th   : 1.82%
  - 75th   : 1.82%
  - 50th   : 1.82%
- SSS vs SSZ:
- depth 0-4
  - average: 9.25%
  - 99th   : 9.25%
  - 95th   : 9.25%
  - 90th   : 9.25%
  - 75th   : 9.25%
  - 50th   : 9.25%
- depth 5
  - average: 9.60%
  - 99th   : 9.25%
  - 95th   : 9.25%
  - 90th   : 9.25%
  - 75th   : 9.25%
  - 50th   : 9.25%
- depth 6
  - average: 15.27%
  - 99th   : 7.50%
  - 95th   : 7.56%
  - 90th   : 7.56%
  - 75th   : 7.64%
  - 50th   : 8.04%
- depth 7
  - average: 10.83%
  - 99th   : 7.56%
  - 95th   : 7.63%
  - 90th   : 7.63%
  - 75th   : 7.63%
  - 50th   : 8.11%
- depth 8
  - average: 9.37%
  - 99th   : 7.56%
  - 95th   : 7.63%
  - 90th   : 7.63%
  - 75th   : 7.63%
  - 50th   : 8.11%
- depth 9
  - average: 7.78%
  - 99th   : 7.69%
  - 95th   : 7.69%
  - 90th   : 7.69%
  - 75th   : 7.69%
  - 50th   : 7.69%


### Discovery Ping

- SSS vs RLP:
  - average: 8.76%
  - 99th   : 7.32%
  - 95th   : 7.32%
  - 90th   : 7.32%
  - 75th   : 7.32%
  - 50th   : 7.32%
- SSS vs SSZ:
  - average: 85.65%
  - 99th   : 83.62%
  - 95th   : 83.62%
  - 90th   : 83.62%
  - 75th   : 83.62%
  - 50th   : 83.62%


### Discovery Pong

- SSS vs RLP:
  - average: 3.92%
  - 99th   : 3.92%
  - 95th   : 3.92%
  - 90th   : 3.92%
  - 75th   : 3.92%
  - 50th   : 3.92%
- SSS vs SSZ:
  - average: 66.89%
  - 99th   : 66.89%
  - 95th   : 66.89%
  - 90th   : 66.89%
  - 75th   : 66.89%
  - 50th   : 66.89%


### Discovery FindNode

- SSS vs RLP:
  - average: 4.11%
  - 99th   : 4.11%
  - 95th   : 4.11%
  - 90th   : 4.11%
  - 75th   : 4.11%
  - 50th   : 4.11%
- SSS vs SSZ:
  - average: 32.69%
  - 99th   : 32.69%
  - 95th   : 32.69%
  - 90th   : 32.69%
  - 75th   : 32.69%
  - 50th   : 32.69%


### Discovery Neighbours

- SSS vs RLP:
  - average: 4.81%
  - 99th   : 4.25%
  - 95th   : 4.28%
  - 90th   : 4.28%
  - 75th   : 4.28%
  - 50th   : 4.79%
- SSS vs SSZ:
  - average: 48.93%
  - 99th   : 48.03%
  - 95th   : 48.08%
  - 90th   : 48.08%
  - 75th   : 48.08%
  - 50th   : 48.99%
