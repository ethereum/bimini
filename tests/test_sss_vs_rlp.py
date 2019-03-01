import codecs
from pathlib import Path

import numpy
import ssz
import rlp

from cytoolz import (
    groupby,
)

from bimini.grammar import parse


def mk_rlp():
    from rlp.sedes import (
        BigEndianInt,
        Binary,
        big_endian_int,
        binary,
        CountableList,
    )
    #
    # RLP
    #
    address = Binary.fixed_length(20, allow_empty=True)
    hash32 = Binary.fixed_length(32)
    uint32 = BigEndianInt(32)
    uint256 = BigEndianInt(256)
    trie_root = Binary.fixed_length(32, allow_empty=True)

    class BlockHeader(rlp.Serializable):
        fields = [
            ('parent_hash', hash32),
            ('uncles_hash', hash32),
            ('coinbase', address),
            ('state_root', trie_root),
            ('transaction_root', trie_root),
            ('receipt_root', trie_root),
            ('bloom', uint256),
            ('difficulty', big_endian_int),
            ('block_number', big_endian_int),
            ('gas_limit', big_endian_int),
            ('gas_used', big_endian_int),
            ('timestamp', big_endian_int),
            ('extra_data', binary),
            ('mix_hash', binary),
            ('nonce', Binary(8, allow_empty=True))
        ]

    class Transaction(rlp.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('gas_price', big_endian_int),
            ('gas', big_endian_int),
            ('to', address),
            ('value', big_endian_int),
            ('data', binary),
            ('v', big_endian_int),
            ('r', big_endian_int),
            ('s', big_endian_int),
        ]

    class Block(rlp.Serializable):
        fields = [
            ('header', BlockHeader),
            ('transactions', CountableList(Transaction)),
            ('uncles', CountableList(BlockHeader))
        ]

    class Log(rlp.Serializable):
        fields = [
            ('address', address),
            ('topics', CountableList(uint32)),
            ('data', binary)
        ]

    class Receipt(rlp.Serializable):
        fields = [
            ('state_root', binary),
            ('gas_used', big_endian_int),
            ('bloom', uint256),
            ('logs', CountableList(Log))
        ]
    return BlockHeader, Block, CountableList(Receipt)


(
    RLPBlockHeader,
    RLPBlock,
    RLPReceipts,
) = mk_rlp()


def mk_ssz():
    #
    # SSZ
    #
    from ssz.sedes import (
        bytes32,
        UInt,
        bytes_sedes,
        List,
    )

    address = bytes_sedes
    uint256 = UInt(2048)
    uint32 = UInt(256)
    big_endian_int = uint32
    trie_root = bytes32
    hash32 = bytes32

    class BlockHeader(ssz.Serializable):
        fields = [
            ('parent_hash', hash32),
            ('uncles_hash', hash32),
            ('coinbase', address),
            ('state_root', trie_root),
            ('transaction_root', trie_root),
            ('receipt_root', trie_root),
            ('bloom', uint256),
            ('difficulty', big_endian_int),
            ('block_number', big_endian_int),
            ('gas_limit', big_endian_int),
            ('gas_used', big_endian_int),
            ('timestamp', big_endian_int),
            ('extra_data', bytes_sedes),
            ('mix_hash', bytes_sedes),
            ('nonce', bytes_sedes),
        ]

    class Transaction(ssz.Serializable):
        fields = [
            ('nonce', big_endian_int),
            ('gas_price', big_endian_int),
            ('gas', big_endian_int),
            ('to', address),
            ('value', big_endian_int),
            ('data', bytes_sedes),
            ('v', big_endian_int),
            ('r', big_endian_int),
            ('s', big_endian_int),
        ]

    class Block(ssz.Serializable):
        fields = [
            ('header', BlockHeader),
            ('transactions', List(Transaction)),
            ('uncles', List(BlockHeader))
        ]

    class Log(ssz.Serializable):
        fields = [
            ('address', address),
            ('topics', List(uint32)),
            ('data', bytes_sedes)
        ]

    class Receipt(ssz.Serializable):
        fields = [
            ('state_root', bytes_sedes),
            ('gas_used', big_endian_int),
            ('bloom', uint256),
            ('logs', List(Log))
        ]
    return BlockHeader, Block, List(Receipt)


(
    SSZBlockHeader,
    SSZBlock,
    SSZReceipts,
) = mk_ssz()


BASE_PATH = Path(__file__).parent


HEADER_PATH = BASE_PATH / 'header.rlp'
BLOCK_PATH = BASE_PATH / 'block.rlp'
RECEIPTS_PATH = BASE_PATH / 'receipts.rlp'


RLP_RAW_HEADER = HEADER_PATH.read_bytes()
RLP_RAW_BLOCK = BLOCK_PATH.read_bytes()
RLP_RAW_RECEIPTS = RECEIPTS_PATH.read_bytes()


RLP_HEADER = rlp.decode(RLP_RAW_HEADER, sedes=RLPBlockHeader)
RLP_BLOCK = rlp.decode(RLP_RAW_BLOCK, sedes=RLPBlock)
RLP_RECEIPTS = rlp.decode(RLP_RAW_RECEIPTS, sedes=RLPReceipts)


sss_header_type_str = '{bytes32,bytes32,bytes20,bytes32,bytes32,bytes32,uint2048,scalar256,scalar256,scalar256,scalar256,scalar256,bytes,bytes,bytes8?}'  # noqa: E501
sss_header_type = parse(sss_header_type_str)
sss_txn_type_str = '{scalar256,scalar256,scalar256,bytes20?,scalar256,bytes,uint8,uint256,uint256}'  # noqa: E501
sss_txn_type = parse(sss_txn_type_str)
sss_block_type_str = '{%s,%s[],%s[]}' % (sss_header_type_str, sss_txn_type, sss_header_type_str)
sss_block_type = parse(sss_block_type_str)
sss_log_type_str = '{bytes20,uint256[],bytes}'
sss_receipt_type_str = '{bytes,scalar256,scalar2048,%s[]}' % sss_log_type_str
sss_receipt_type = parse(sss_receipt_type_str)
sss_receipts_type = parse('%s[]' % sss_receipt_type_str)


SSS_RAW_HEADER = sss_header_type.encode(RLP_HEADER)
SSS_RAW_BLOCK = sss_block_type.encode(RLP_BLOCK)
SSS_RAW_RECEIPTS = sss_receipts_type.encode(RLP_RECEIPTS)


SSZ_RAW_HEADER = ssz.encode(RLP_HEADER, sedes=SSZBlockHeader)
SSZ_RAW_BLOCK = ssz.encode(RLP_BLOCK, sedes=SSZBlock)
SSZ_RAW_RECEIPTS = ssz.encode(RLP_RECEIPTS, sedes=SSZReceipts)


DISC_V4_MESSAGES_PATH = BASE_PATH / 'discv4.rlp'
RAW_DISC_V4_MESSAGES = DISC_V4_MESSAGES_PATH.read_text().splitlines()


def mk_rlp_disc():
    from rlp.sedes import (
        binary,
        CountableList,
        big_endian_int,
    )

    class Address(rlp.Serializable):
        fields = [
            ('sender_ip', binary),
            ('sender_udp_port', big_endian_int),
            ('sender_tcp_port', big_endian_int),
        ]

    class Ping(rlp.Serializable):
        fields = [
            ('version', big_endian_int),
            ('from', Address),
            ('to', Address),
            ('expiration', big_endian_int),
        ]

    class Pong(rlp.Serializable):
        fields = [
            ('to', Address),
            ('ping_hash', binary),
            ('expiration', big_endian_int),
        ]

    class FindNode(rlp.Serializable):
        fields = [
            ('target', binary),
            ('expiration', big_endian_int),
        ]

    class Neighbour(rlp.Serializable):
        fields = [
            ('ip', binary),
            ('udp_port', big_endian_int),
            ('tcp_port', big_endian_int),
            ('node_id', binary),
        ]

    class Neighbours(rlp.Serializable):
        fields = [
            ('nodes', CountableList(Neighbour)),
            ('expiration', big_endian_int),
        ]

    return Ping, Pong, FindNode, Neighbours


(
    RLPPing,
    RLPPong,
    RLPFindNode,
    RLPNeighbours,
) = mk_rlp_disc()


def decode_discovery_message(data):
    try:
        return rlp.decode(data, sedes=RLPPing)
    except rlp.exceptions.RLPException:
        pass

    try:
        return rlp.decode(data, sedes=RLPPong)
    except rlp.exceptions.RLPException:
        pass

    try:
        return rlp.decode(data, sedes=RLPFindNode)
    except rlp.exceptions.RLPException:
        pass

    try:
        return rlp.decode(data, sedes=RLPNeighbours)
    except rlp.exceptions.RLPException:
        pass

    raise Exception("Couldn't decode message")


RLP_RAW_DISC_V4_MESSAGES = tuple(map(lambda msg: codecs.decode(msg, 'hex'), RAW_DISC_V4_MESSAGES))
RLP_DISC_V4_MESSAGES = tuple(map(decode_discovery_message, RLP_RAW_DISC_V4_MESSAGES))

RLP_DISC_V4_BY_TYPE = groupby(type, RLP_DISC_V4_MESSAGES)
RLP_RAW_DISC_V4_BY_TYPE = {
    rlp_type: tuple(rlp.encode(msg, sedes=rlp_type) for msg in msgs)
    for rlp_type, msgs
    in RLP_DISC_V4_BY_TYPE.items()
}


sss_address_type_str = '{bytes,scalar16,scalar16}'
sss_ping_type_str = '{scalar8,%s,%s,scalar32}' % (sss_address_type_str, sss_address_type_str)
sss_ping_type = parse(sss_ping_type_str)
sss_pong_type_str = '{%s,bytes,scalar32}' % sss_address_type_str
sss_pong_type = parse(sss_pong_type_str)
sss_find_node = parse('{bytes,scalar32}')
sss_neighbor_type_str = '{bytes,scalar16,scalar16,bytes}'
sss_neighbors_type_str = '{%s[],scalar32}' % sss_neighbor_type_str
sss_neighbors_type = parse(sss_neighbors_type_str)


RLP_DISC_V4_TO_SSS_LOOKUP = {
    RLPPing: sss_ping_type,
    RLPPong: sss_pong_type,
    RLPFindNode: sss_find_node,
    RLPNeighbours: sss_neighbors_type,
}


def chain_data_meta():
    print("Chain Data test vectors:")
    print("==========")
    print(f"block #{RLP_HEADER.block_number}:")
    print(f" - txns        : {len(RLP_BLOCK[1])}")
    print(f" - uncles      : {len(RLP_BLOCK[2])}")
    print("receipts:")
    print(f" - num         : {len(RLP_RECEIPTS)}")


def chain_data_rlp_meta():
    print("RLP info:")
    print("==========")
    print("header:")
    print(f" - size        : {len(RLP_RAW_HEADER)}")
    print("block:")
    print(f" - size        : {len(RLP_RAW_BLOCK)}")
    print("receipts:")
    print(f" - total-size  : {len(RLP_RAW_RECEIPTS)}")
    print(f" - avg-size    : {len(RLP_RAW_RECEIPTS) // len(RLP_RECEIPTS)}")


def chain_data_sss_meta():
    print('SSS info')
    print("==========")
    print("header:")
    print(f" - size        : {len(SSS_RAW_HEADER)}")
    print("block:")
    print(f" - size        : {len(SSS_RAW_BLOCK)}")
    print("receipts:")
    print(f" - total-size  : {len(SSS_RAW_RECEIPTS)}")
    print(f" - avg-size    : {len(SSS_RAW_RECEIPTS) // len(RLP_RECEIPTS)}")


def chain_data_ssz_meta():
    print('SSZ info')
    print("==========")
    print("header:")
    print(f" - size        : {len(SSZ_RAW_HEADER)}")
    print("block:")
    print(f" - size        : {len(SSZ_RAW_BLOCK)}")
    print("receipts:")
    print(f" - total-size  : {len(SSZ_RAW_RECEIPTS)}")
    print(f" - avg-size    : {len(SSZ_RAW_RECEIPTS) // len(RLP_RECEIPTS)}")


def chain_data_summary():
    sss_to_rlp_header_percent = 100 * len(SSS_RAW_HEADER) / len(RLP_RAW_HEADER)
    sss_to_rlp_block_percent = 100 * len(SSS_RAW_BLOCK) / len(RLP_RAW_BLOCK)
    sss_to_rlp_receipts_percent = 100 * len(SSS_RAW_RECEIPTS) / len(RLP_RAW_RECEIPTS)

    sss_to_ssz_header_percent = 100 * len(SSS_RAW_HEADER) / len(SSZ_RAW_HEADER)
    sss_to_ssz_block_percent = 100 * len(SSS_RAW_BLOCK) / len(SSZ_RAW_BLOCK)
    sss_to_ssz_receipts_percent = 100 * len(SSS_RAW_RECEIPTS) / len(SSZ_RAW_RECEIPTS)

    print('Summary')
    print("==========")
    print("SSS sizes compared to RLP sizes")
    print(f"header  : {sss_to_rlp_header_percent:.2f}%")
    print(f"block   : {sss_to_rlp_block_percent:.2f}%")
    print(f"receipts: {sss_to_rlp_receipts_percent:.2f}%")
    print("\n")
    print("SSS sizes compared to SSZ sizes")
    print(f"header  : {sss_to_ssz_header_percent:.2f}%")
    print(f"block   : {sss_to_ssz_block_percent:.2f}%")
    print(f"receipts: {sss_to_ssz_receipts_percent:.2f}%")


def disc_v4_meta():
    print("RLP DISCOVERY: meta")
    print("===================")
    for msg_type, msgs in RLP_DISC_V4_BY_TYPE.items():
        name = msg_type.__name__.lower()
        print(f"{name.ljust(10)}: {len(msgs)}")


def rlp_disc_v4():
    print("RLP DISCOVERY: info")
    print("===================")
    for msg_type, msgs in RLP_DISC_V4_BY_TYPE.items():
        name = msg_type.__name__.lower()
        encoded_msgs = RLP_RAW_DISC_V4_BY_TYPE[msg_type]
        avg_size = int(sum((len(data) for data in encoded_msgs)) / len(msgs))
        print(f" -{name}")
        print(f"   - sizes    : {' | '.join(set((str(len(data)) for data in encoded_msgs)))}")
        print(f"   - avg size : {avg_size}")


def sss_disc_v4():
    print("SSS DISCOVERY: info")
    print("===================")
    for msg_type, msgs in RLP_DISC_V4_BY_TYPE.items():
        name = msg_type.__name__.lower()

        sss_type = RLP_DISC_V4_TO_SSS_LOOKUP[msg_type]
        sss_raw_msgs = tuple(sss_type.encode(msg) for msg in msgs)
        avg_size = int(sum((len(data) for data in sss_raw_msgs)) / len(msgs))
        print(f" - {name}")
        print(f"   - sizes    : {' | '.join(set((str(len(data)) for data in sss_raw_msgs)))}")
        print(f"   - avg size : {avg_size}")


def disc_v4_summary():
    print('Summary')
    print("==========")
    print(f"SSS sizes compared to RLP")

    for msg_type, msgs in RLP_DISC_V4_BY_TYPE.items():
        name = msg_type.__name__.lower()
        rlp_raw_msgs = RLP_RAW_DISC_V4_BY_TYPE[msg_type]

        sss_type = RLP_DISC_V4_TO_SSS_LOOKUP[msg_type]
        sss_raw_msgs = tuple(sss_type.encode(msg) for msg in msgs)

        sss_sizes = tuple(len(data) for data in sss_raw_msgs)
        rlp_sizes = tuple(len(data) for data in rlp_raw_msgs)

        size_percentages = tuple(
            100 * sss_size / rlp_size
            for sss_size, rlp_size
            in zip(sss_sizes, rlp_sizes)
        )
        relative_99th = numpy.percentile(size_percentages, 99)
        relative_90th = numpy.percentile(size_percentages, 90)
        relative_75th = numpy.percentile(size_percentages, 75)
        relative_50th = numpy.percentile(size_percentages, 50)

        avg_sss_size = int(sum(sss_sizes) / len(msgs))
        avg_rlp_size = int(sum(rlp_sizes) / len(msgs))

        sss_to_rlp_percent = 100 * avg_sss_size / avg_rlp_size

        print(f"{name.ljust(10)} : avg={sss_to_rlp_percent:.2f}%  99th={relative_99th:.2f}  90th={relative_90th:.2f}  75th={relative_75th:.2f}  50th={relative_50th:.2f}")  # noqa: E501

# import pdb; pdb.set_trace()


if __name__ == '__main__':
    chain_data_meta()
    print('\n')
    chain_data_rlp_meta()
    print('\n')
    chain_data_sss_meta()
    print('\n')
    chain_data_ssz_meta()
    print('\n')
    chain_data_summary()
    print('\n')
    disc_v4_meta()
    print('\n')
    rlp_disc_v4()
    print('\n')
    sss_disc_v4()
    print('\n')
    disc_v4_summary()

