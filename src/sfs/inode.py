from enum import Enum


class INodeError:
    """
    General error for the INode class.
    """


class FileType(Enum):
    DIR = 1
    REG = 2


class INode:
    def __init__(self, file_type: FileType=FileType.REG):
        self.file_type: FileType = file_type
        self.data_blocks: list = []

    def serialize(self):
        b = bytearray()

        b.append(self.file_type.value)
        b.extend(self.data_blocks)

        return b
