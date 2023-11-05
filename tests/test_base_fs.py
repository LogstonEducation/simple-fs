import pytest

from sfs.fs import BaseFS, SimpleFSError


def get_raw_disk(blocks=10, block_size=32) -> bytearray:
    b = bytearray()

    for i in range(blocks):
        b.extend(i for _ in range(block_size))

    return b


def test_init():
    raw_disk = bytearray()
    with pytest.raises(SimpleFSError):
        BaseFS(raw_disk, block_size=32)

    raw_disk = bytearray([0])
    with pytest.raises(SimpleFSError):
        BaseFS(raw_disk, block_size=32)


def test_set_block():
    raw_disk = get_raw_disk()

    assert raw_disk[5*32:6*32] == b'\x05' * 32

    fs = BaseFS(raw_disk, block_size=32)

    with pytest.raises(SimpleFSError):
        fs._set_block(5, bytes(1 for _ in range(1000)))

    fs._set_block(5, bytes([1, 2, 3]))

    assert raw_disk[5*32:6*32] == b'\x01\x02\x03' + b'\x00' * 29


def test_get_block():
    raw_disk = get_raw_disk()
    fs = BaseFS(raw_disk, block_size=32)

    fs._set_block(5, bytes([1, 2, 3]))
    assert fs._get_block(1) == b'\x01' * 32
    assert fs._get_block(5) == b'\x01\x02\x03' + b'\x00' * 29


def test_serialize():
    raw_disk = get_raw_disk()
    fs = BaseFS(raw_disk, block_size=32)
    assert fs.serialize() == get_raw_disk()
