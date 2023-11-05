import pytest

from sfs.bitmap import Bitmap, BitmapError


def setup_bitmap():
    raw_disk = bytearray(0 for _ in range(16))
    bitmap_slice = slice(4, 15)

    return Bitmap(raw_disk, bitmap_slice)


def test_noop():
    bm = setup_bitmap()

    expected = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected


def test_reserve():
    bm = setup_bitmap()

    bm.reserve(18)
    expected = b'\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected

    # Repeats are not okay.
    with pytest.raises(BitmapError):
        bm.reserve(18)

    bm.reserve(0)
    expected = b'\x00\x00\x00\x00\x01\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected


def test_release():
    bm = setup_bitmap()

    bm.reserve(18)
    expected = b'\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected

    bm.release(18)
    expected = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected

    # Releasing an unused block is not okay.
    with pytest.raises(BitmapError):
        bm.release(18)

    for i in range(24, 29):
        bm.reserve(i)
    expected = b'\x00\x00\x00\x00\x00\x00\x00\x1f\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected

    bm.release(27)
    expected = b'\x00\x00\x00\x00\x00\x00\x00\x17\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected

    with pytest.raises(BitmapError):
        bm.release(200)


def test_first_free_bit():
    bm = setup_bitmap()

    assert bm._first_free_bit(0) == 0
    assert bm._first_free_bit(1) == 1
    assert bm._first_free_bit(3) == 2
    assert bm._first_free_bit(7) == 3
    assert bm._first_free_bit(15) == 4
    assert bm._first_free_bit(31) == 5
    assert bm._first_free_bit(63) == 6
    assert bm._first_free_bit(127) == 7
    assert bm._first_free_bit(255) == 8

    assert bm._first_free_bit(19) == 2


def test_find_free():
    bm = setup_bitmap()

    assert bm._find_free_block_index() == 0

    bm._raw_disk[bm._bitmap_slice.start] = 255
    assert bm._find_free_block_index() == 8, bm._raw_disk

    bm._raw_disk[bm._bitmap_slice.start + 1] = 255
    assert bm._find_free_block_index() == 16, bm._raw_disk

    bm._raw_disk[bm._bitmap_slice.start + 2] = 19
    assert bm._find_free_block_index() == 18, bm._raw_disk


def test_next():
    bm = setup_bitmap()

    # (15 - 4) * 8 == 88
    for i in range(88):
        assert bm.next() == i

    with pytest.raises(BitmapError):
        bm.next()


def test_reset():
    bm = setup_bitmap()

    for i in range(0, 88, 3):
        bm.reserve(i)

    expected = b'\x00\x00\x00\x00I\x92$I\x92$I\x92$I\x92\x00'
    assert bm._raw_disk == expected

    bm.reset()

    expected = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    assert bm._raw_disk == expected
