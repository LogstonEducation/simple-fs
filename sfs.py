"""
A very Simple File System (SFS).

Based off of the contents of Chapter 40 in OSTEP [1].


The file system is made up of a super node block, several blocks of index nodes
(inodes), even more blocks of data, and bitmaps to indicate which blocks are
available.


[1]
"""


class SimpleFSError(Exception):
    """
    General error for SimpleFS class.
    """


class INode:
    def __init__(self, sfs):
        self.sfs = sfs


class Bitmap:
    def __init__(self, raw_disk: bytearray, bitmap_slice: slice) -> None:
        self._raw_disk = raw_disk
        self._bitmap_slice = bitmap_slice

    def next(self):
        """
        Reserve and return next available free block.
        """

    def reserve(self, bitmap_slice: slice):
        """
        Mark blocks indicated by bitmap_slice as in use.
        """
        data = self._raw_disk[self._bitmap_slice]



    def release(self, bitmap_slice: slice):
        """
        Mark blocks indicated by bitmap_slice as free for use.
        """




class SimpleFS:
    SUPER_NODE_INDEX = 0
    # Offset from start of SUPER_NODE_INDEX into raw disk.
    INDEX_NODE_OFFSET = 1

    __SUPERNODE_INFO_MAGIC_INDEX = slice(0, 3)
    __SUPERNODE_INFO_MAGIC_VALUE = b'SFS'
    __SUPERNODE_INFO_INODE_BLOCK_SIZE_INDEX = 4

    def __init__(self, raw_disk: bytearray, block_size: int=32) -> None:
        """
        Create a simple file system.
        """
        self._raw_disk = raw_disk
        self.block_size = block_size

        if len(self._raw_disk) % block_size != 0:
            raise SimpleFSError(
                f'Invalid disk size (len({raw_disk})) for given block size ({block_size})'
            )

        if len(self._raw_disk) < 5 * block_size:
            raise SimpleFSError(
                f'Disk too small (len({raw_disk})) for given block size ({block_size})'
            )

    def _set_block(self, index: int, data: bytes):
        """
        Set data at index. Pad data as required.
        """
        if len(data) > self.block_size:
            raise SimpleFSError(
                f'Data length too large (len({data})) for given block size ({self.block_size})'
            )

        data = bytearray(data)

        padding = (self.block_size - len(data))
        for _ in range(padding):
            data.append(0)

        self._raw_disk[index:index+self.block_size] = data

    def _get_block(self, index: int) -> bytes:
        return self._raw_disk[index:index+self.block_size]

    def _index_node_bitmap_slice(self) -> slice:
        super_node = self._get_block(self.SUPER_NODE_INDEX)
        assert super_node[self.__SUPERNODE_INFO_MAGIC_INDEX] == self.__SUPERNODE_INFO_MAGIC_VALUE

        start = (self.SUPER_NODE_INDEX + self.INDEX_NODE_OFFSET) * self.block_size
        width = (super_node[self.__SUPERNODE_INFO_INODE_BLOCK_SIZE_INDEX] * self.block_size)

        return slice(start, start + width)

    @property
    def index_node_bitmap(self) -> Bitmap:
        return Bitmap(self._raw_disk, self._index_node_bitmap_slice())

    @property
    def data_node_bitmap_index(self):
        return self.DATA_NODE_BITMAP_INDEX * self.block_size

    def format(self):
        """
        Reset disk's inode data.
        """
        self._reset_super_ndoe()
        self._reset_bitmaps()

    def _reset_super_ndoe(self):
        data = bytearray()
        data[0:3] = b'SFS'  # Magic number of SimpleFS
        data[4] = 1  # Number of blocks for inode bitmap
        data[5] = 1  # Number of blocks for data node bitmap

        self._set_block(self.SUPER_NODE_INDEX, bytes(data))

    def _reset_bitmaps(self):
        self._set_block(self.index_node_bitmap_index, bytes())
        self._set_block(self.data_node_bitmap_index, bytes())

    def _next_free_bitmap_index(self, index):

        self.super_node_index

        self.INDEX_NODE_BITMAP_INDEX[]



        pass

    def serialize(self) -> bytes:
        return bytes(self._raw_disk)

    def open(self, name: bytes) -> INode:
        """
        Return an i-node (instead of a file descriptor) to the file referenced by "name".
        """
        # Walk the path to correct file.
        # Find i-node for file.

        # If file is directory, read data blocks.
        # Inode index + file name + null terminator

        # Root is inode 0, directory contents of root are held in blocks identifeid by inode 0

        # inode holds type of file, and up to three pointers to data blocks

        return INode(self, 'inode data')
