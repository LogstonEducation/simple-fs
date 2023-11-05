"""
A very Simple File System (SFS).

Based off of the contents of Chapter 40 in OSTEP [1].


The file system is made up of a super block, several blocks of index nodes
(inodes), even more blocks of data, and bitmaps to indicate which blocks are
available.


[1]
"""

from .bitmap import Bitmap
from .inode import FileType, INode


class SimpleFSError(Exception):
    """
    General error for SimpleFS class.
    """


class BaseFS:
    def __init__(self, raw_disk: bytearray, block_size: int=32) -> None:
        self._raw_disk = raw_disk
        self.block_size = block_size

        if len(self._raw_disk) % block_size != 0:
            raise SimpleFSError(
                f'Invalid disk size ({len(raw_disk)}) for given block size ({block_size})'
            )

        if len(self._raw_disk) < 5 * block_size:
            raise SimpleFSError(
                f'Disk too small ({len(raw_disk)}) for given block size ({block_size})'
            )

    def _get_block_slice_by_index(self, index: int) -> slice:
        start = index * self.block_size
        end = start + self.block_size
        return slice(start, end)

    def _set_block(self, index: int, data: bytes):
        """
        Set data at index. Pad data as required.
        """
        if len(data) > self.block_size:
            raise SimpleFSError(
                f'Data length too large ({len(data)}) for given block size ({self.block_size})'
            )

        data = bytearray(data)

        padding = (self.block_size - len(data))
        for _ in range(padding):
            data.append(0)

        self._raw_disk[self._get_block_slice_by_index(index)] = data

    def _get_block(self, index: int) -> bytes:
        return self._raw_disk[self._get_block_slice_by_index(index)]

    def serialize(self) -> bytes:
        return bytes(self._raw_disk)


class MetadataMixin(BaseFS):
    SUPER_BLOCK_INDEX = 0
    # Offset from start of SUPER_BLOCK_INDEX into raw disk.
    INDEX_NODE_OFFSET = 1

    SUPER_BLOCK_INFO_MAGIC_INDEX = slice(0, 3)
    SUPER_BLOCK_INFO_MAGIC_VALUE = b'SFS'  # Magic number of SimpleFS
    SUPER_BLOCK_INFO_INODE_BLOCK_SIZE_INDEX = 4
    SUPER_BLOCK_INFO_INODE_BLOCK_COUNT_INDEX = 6
    SUPER_BLOCK_INFO_DATA_BLOCK_SIZE_INDEX = 5
    SUPER_BLOCK_INFO_DATA_BLOCK_COUNT_INDEX = 7

    @property
    def _super_block(self):
        block = self._get_block(self.SUPER_BLOCK_INDEX)
        assert block[self.SUPER_BLOCK_INFO_MAGIC_INDEX] == self.SUPER_BLOCK_INFO_MAGIC_VALUE
        return block

    def _reset_super_block(self):
        data = bytearray(0 for _ in range(self.block_size))
        data[self.SUPER_BLOCK_INFO_MAGIC_INDEX] = self.SUPER_BLOCK_INFO_MAGIC_VALUE
        data[self.SUPER_BLOCK_INFO_INODE_BLOCK_SIZE_INDEX] = 1  # Number of blocks for inode bitmap
        data[self.SUPER_BLOCK_INFO_DATA_BLOCK_SIZE_INDEX] = 1  # Number of blocks for data node bitmap
        data[self.SUPER_BLOCK_INFO_INODE_BLOCK_COUNT_INDEX] = 8  # Number of blocks for inodes
        data[self.SUPER_BLOCK_INFO_DATA_BLOCK_COUNT_INDEX] = 54  # Number of blocks for data blocks

        self._set_block(self.SUPER_BLOCK_INDEX, bytes(data))

    def _inode_bitmap_slice(self) -> slice:
        start = (self.SUPER_BLOCK_INDEX + self.INDEX_NODE_OFFSET) * self.block_size
        width = (self._super_block[self.SUPER_BLOCK_INFO_INODE_BLOCK_SIZE_INDEX] * self.block_size)

        return slice(start, start + width)

    @property
    def index_node_bitmap(self) -> Bitmap:
        return Bitmap(self._raw_disk, self._inode_bitmap_slice())

    def _data_bitmap_slice(self) -> slice:
        index_node_bitmap = self._inode_bitmap_slice()
        start = index_node_bitmap.stop

        width = (self._super_block[self.SUPER_BLOCK_INFO_DATA_BLOCK_SIZE_INDEX] * self.block_size)

        return slice(start, start + width)

    @property
    def data_node_bitmap(self) -> Bitmap:
        return Bitmap(self._raw_disk, self._data_bitmap_slice())

    def _to_raw_block_index(self, index: int, data_block=True) -> int:
        # Values are in terms of blocks, not bytes.
        inode_start = int(self._data_bitmap_slice().stop / self.block_size)
        inode_count = self._super_block[self.SUPER_BLOCK_INFO_INODE_BLOCK_COUNT_INDEX]

        data_block_start = inode_start + inode_count
        data_block_count = self._super_block[self.SUPER_BLOCK_INFO_DATA_BLOCK_COUNT_INDEX]

        if data_block:
            if index > data_block_count:
                raise SimpleFSError(f'Index {index} out of range of data nodes')

            return index + data_block

        # Is INode
        if index > (data_block_start - inode_start):
            raise SimpleFSError(f'Index {index} out of range of inodes')

        return index + inode_start

    def _get_inode_block(self, index: int) -> bytes:
        return self._get_block(self._to_raw_block_index(index, data_block=False))

    def _set_inode_block(self, index: int, data: bytes):
        self._set_block(self._to_raw_block_index(index, data_block=False), data)

    def _get_data_block(self, index: int) -> bytes:
        return self._get_block(self._to_raw_block_index(index, data_block=True))

    def _set_data_block(self, index: int, data: bytes):
        self._set_block(self._to_raw_block_index(index, data_block=True), data)

    def format(self):
        """
        Reset disk's bitmaps and super_block.
        """
        self._reset_super_block()
        self.index_node_bitmap.reset()
        self.data_node_bitmap.reset()

        # Create a root dir.
        data_block_index = self.data_node_bitmap.next()
        self._set_data_block(data_block_index, b'')

        inode = INode()
        inode.file_type = FileType.DIR
        inode.data_blocks.append(data_block_index)
        inode_block_index = self.index_node_bitmap.next()
        # Write inode to FIRST block in inodes block list.
        assert inode_block_index == 0
        self._set_inode_block(inode_block_index, inode.serialize())

    def _get_data_for_inode(self, inode: INode) -> bytes:
        data = bytearray()
        for data_block_id in inode.data_blocks:
            data.extend(self._get_data_block(data_block_id))
        return data

    def _parse_dir_data(self, data: bytes) -> dict:
        return {data[i+1:i+8]: data[i] for i in range(0, len(data), 8)}

    def _serialize_dir_data(self, data: dict) -> bytes:
        b = bytearray()
        for key, value in sorted(data.items()):
            b.append(key)

            if len(value) > 7:
                raise SimpleFSError(f'File name "{value}" too long {len(value)}')

            b.extend(value)
            for _ in range(7 - len(value)):
                b.append(0)

        return bytes(b)

    def _get_inode_block_from_dir_data(self, data: bytes, name: bytes) -> int:
        for inode_block_index, file_name in self._parse_dir_data(data).items():
            if name == file_name:
                return inode_block_index

        raise FileNotFoundError(name)


class SimpleFS(MetadataMixin):

    def open(self, name: bytes) -> INode:
        """
        Return an i-node (instead of a file descriptor) to the file referenced by "name".
        """
        name = name.lstrip(b'/')

        inode_block_index = 0
        while True:
            inode = INode.parse(self._get_inode_block(inode_block_index))  # Start at root node.
            if inode.file_type == FileType.REG:
                return inode

            data = self._get_data_for_inode(inode)

            name_part = name[:name.find(b'/')]
            name = name[name.find(b'/')+1:]

            inode_block_index = self._get_inode_block_from_dir_data(data, name_part)
