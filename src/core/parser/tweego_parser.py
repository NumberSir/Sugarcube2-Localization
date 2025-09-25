# """https://github.com/tmedwards/tweego/blob/master/internal/tweelexer/tweelexer.go"""
# from itertools import count
# from typing import TypeAlias
# from enum import Enum, auto
# from pydantic import BaseModel, Field
#
#
# EOF: int = -1
#
#
# class ItemType(Enum):
#     ItemError = auto()      # Error.  Its value is the error message.
#     ItemEOF = auto()        # End of input.
#     ItemHeader = auto()     # '::', but only when starting a line.
#     ItemName = auto()       # Text w/ backslash escaped characters.
#     ItemTags = auto()       # '[tag1 tag2 tagN]'.
#     ItemMetadata = auto()   # JSON chunk, '{…}'.
#     ItemContent = auto()    # Plain text.
#
#
# class Item:
#     def __init__(self, type_: ItemType = None, line: int = None, pos: int = None, val: str = None):
#         self._type: ItemType = type_    # Type of the item.
#         self._line: int = line          # Line within the input (1-base) of the item.
#         self._pos: int = pos            # Starting position within the input, in bytes, of the item.
#         self._val: str = val            # Value of the item.
#
#     def __repr__(self):
#         return self.__str__()
#
#     def __str__(self):
#         name: str = ""
#         match self.type:
#             case ItemType.ItemEOF:
#                 return f"[EOF: {self.line}/{self.pos}]"
#             case ItemType.ItemError:
#                 name = "Error"
#             case ItemType.ItemHeader:
#                 name = "Header"
#             case ItemType.ItemName:
#                 name = "Name"
#             case ItemType.ItemTags:
#                 name = "Tags"
#             case ItemType.ItemMetadata:
#                 name = "Metadata"
#             case ItemType.ItemContent:
#                 name = "Content"
#
#         if self.type != ItemType.ItemError and len(self.val) > 80:
#             return f"[{name}: {self.line}/{self.pos}] {self.val:.80}%..."
#         return  f"[{name}: {self.line}/{self.pos}] {self.val}%..."
#
#     @property
#     def type(self):
#         return self._type
#
#     @property
#     def line(self):
#         return self._line
#
#     @property
#     def pos(self):
#         return self._pos
#
#     @property
#     def val(self):
#         return self._val
#
#
# class Lexer:
#     def __init__(self, input_: str = None, line: int = None, start: int = None, pos: int = None, items: Item = None):
#         self._input: str = input_   # Byte slice being scanned.
#         self._line: int = line      # Number of newlines seen (1-base).
#         self._start: int = start    # Starting position of the current item.
#         self._pos: int = pos        # Current position within the input.
#         self._items: Item = items   # Channel of scanned items.
#
#     def next(self) -> str:
#         if self.pos >= len(self.input):
#             return EOF
#
#         char = self.input[self.pos]
#         self.pos += 1
#
#         if char == "\n":
#             self.line += 1
#         return char
#
#     def peek(self) -> str:
#         return EOF if self.pos >= len(self.input) else self.input[self.pos]
#
#     def backup(self) -> None:
#         if self.pos <= self.start:
#             raise Exception("backup would leave `pos` < `start`")
#
#         self.pos -= 1
#         if self.input[self.pos] == "\n":
#             self.line -= 1
#
#     def emit(self, type_: ItemType) -> None:
#         """TODO"""
#         pass
#
#     def ignore(self) -> None:
#         self.line += len(self.input.count("\n", self.start, self.pos))
#         self.start = self.pos
#
#     def accept(self, valid: str) -> bool:
#         if self.next in valid:
#             return True
#         self.backup()
#         return False
#
#     def accept_run(self, valid: str) -> None:
#         char = self.next()
#         while char in valid:
#             char = self.next()
#
#         if char != EOF:
#             self.backup()
#
#     @property
#     def input(self):
#         return self._input
#
#     @property
#     def line(self):
#         return self._line
#
#     @line.setter
#     def line(self, line: int):
#         self._line = line
#
#     @property
#     def start(self):
#         return self._start
#
#     @start.setter
#     def start(self, start: int):
#         self._start = start
#
#     @property
#     def pos(self):
#         return self._pos
#
#     @pos.setter
#     def pos(self, pos: int):
#         self._pos = pos
#
#     @property
#     def items(self):
#         return self._items
#
#     @items.setter
#     def items(self, item: Item):
#         self._items = item
