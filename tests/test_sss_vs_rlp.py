from pathlib import Path

import rlp


BASE_PATH = Path(__file__).parent


HEADER_PATH = BASE_PATH / 'header.rlp'
BLOCK_PATH = BASE_PATH / 'block.rlp'
RECEIPTS_PATH = BASE_PATH / 'receipts.rlp'


RAW_HEADER = HEADER_PATH.read_bytes()
RAW_BLOCK = BLOCK_PATH.read_bytes()
RAW_RECEIPTS = RECEIPTS_PATH.read_bytes()


HEADER = rlp.decode(RAW_HEADER)
BLOCK = rlp.decode(RAW_BLOCK)
RECEIPTS = rlp.decode(RAW_RECEIPTS)


def rlp_meta():
    print("RLP Sizes:")
    print("==========")
    print("header:")
    print(f" - size        : {len(RAW_HEADER)}")
    print("block:")
    print(f" - size        : {len(RAW_BLOCK)}")
    print(f" - txns        : {len(BLOCK[1])}")
    print(f" - uncles      : {len(BLOCK[2])}")
    print("receipts:")
    print(f" - total-size  : {len(RAW_RECEIPTS)}")
    print(f" - num         : {len(RECEIPTS)}")
    print(f" - avg-size    : {len(RAW_RECEIPTS) // len(RECEIPTS)}")


if __name__ == '__main__':
    rlp_meta()
