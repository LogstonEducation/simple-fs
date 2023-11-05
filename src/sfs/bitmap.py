class BitmapError(Exception):
    """
    General error for the Bitmap class.
    """


class Bitmap:
    """
    A class to represent the bitmap used to track free blocks.
    """
    def __init__(self, raw_disk: bytearray, bitmap_slice: slice) -> None:
        self._raw_disk = raw_disk
        self._bitmap_slice = bitmap_slice

    def next(self) -> int:
        """
        Reserve and return next available free block.
        """
        block_index = self._find_free_block_index()
        self.reserve(block_index)
        return block_index

    def _find_free_block_index(self):
        """
        Find the next available block.
        """
        # Each bit in data corresponds to a block. There are 8 bits to a byte
        # and there are several bytes in a block (>~32). Thus we have ~256
        # blocks we can allocate with a single-block bitmap.
        index = 0
        for byte_index in range(self._bitmap_slice.start, self._bitmap_slice.stop):
            i = self._first_free_bit(self._raw_disk[byte_index])
            index += i

            if i < 8:
                break

        return index

    @staticmethod
    def _first_free_bit(b: int) -> int:
        for i in range(8):
            if ((b >> i) & 0b1) == 0:
                return i

        return 8

    def reserve(self, block_index: int):
        """
        Mark block indicated by index as in use.
        """
        # Get bitmap for given byte index.
        byte_index = self._bitmap_slice.start + int(block_index / 8)
        if byte_index >= self._bitmap_slice.stop:
            raise BitmapError(f'Block at index {block_index} too large')

        byte = self._raw_disk[byte_index]

        # Find offset in byte to flip bit.
        bit_index = (block_index % 8)

        # Safety check.
        if (byte & (0b1 << bit_index)):
            raise BitmapError(f'Block at index {block_index} already reserved')

        # Flip bit in correct position.
        byte |= (0b1 << bit_index)

        # Save work.
        self._raw_disk[byte_index] = byte

    def release(self, block_index: int):
        """
        Mark block indicated by index as free for use.
        """
        # Get bitmap for given byte index.
        byte_index = self._bitmap_slice.start + int(block_index / 8)
        if byte_index >= self._bitmap_slice.stop:
            raise BitmapError(f'Block at index {block_index} too large')

        byte = self._raw_disk[byte_index]

        # Find offset in byte to flip bit.
        bit_index = (block_index % 8)

        # Safety check.
        if not (byte & (0b1 << bit_index)):
            raise BitmapError(f'Block at index {block_index} already released')

        # Flip bit in correct position.
        byte ^= (0b1 << bit_index)

        # Save work.
        self._raw_disk[byte_index] = byte

    def reset(self):
        """
        Reset all bits for all blocks to zero.
        """
        for byte_index in range(self._bitmap_slice.start, self._bitmap_slice.stop):
            self._raw_disk[byte_index] = 0
