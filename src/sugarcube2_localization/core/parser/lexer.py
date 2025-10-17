# """src/markup/lexer.js"""
# from collections.abc import Callable
# from enum import Enum
# from typing import TypeAlias
# from src.core.schema.model import LexerDataModel, LexerItemModel
#
# State: TypeAlias = Callable[["Lexer"], ...]
#
#
# class Lexer:
#     EOF: int = -1
#
#     def __init__(self, source: str, initial_state: State):
#         self._source: str = source  # the string to be scanned
#         self._initial: State = initial_state  # initial state
#         self._state: State = initial_state  # current state
#         self._start: int = 0  # start position of an item
#         self._pos: int = 0  # current position in the source string
#         self._depth: int = 0  # current brace/bracket/parenthesis nesting depth
#         self._items: list[LexerItemModel] = []  # scanned item queue
#         self._data: LexerDataModel = None  # lexing data
#
#     def reset(self) -> None:
#         self._state = self._initial
#         self._start = 0
#         self._pos = 0
#         self._depth = 0
#         self._items = []
#         self._data = None
#
#     def run(self) -> list[LexerItemModel]:
#         # scan the source string until no states remain
#         while self._state:
#             self._state = self._state(self)
#         # return the array of items
#         return self.items
#
#     def next(self) -> int | str:
#         if self._pos >= len(self._source):
#             return self.EOF
#
#         next_ = self._source[self._pos]
#         self._pos += 1
#         return next_
#
#     def peek(self) -> int | str:
#         return self.EOF if self._pos >= len(self._source) else self._source[self._pos]
#
#     def backup(self, number: int = None) -> None:
#         self._pos -= number or 1
#
#     def forward(self, number: int = None) -> None:
#         self._pos += number or 1
#
#     def ignore(self) -> None:
#         self._start = self._pos
#
#     def accept(self, valid: str = None) -> bool:
#         if valid is None: raise NotImplementedError
#         char = self.next()
#         if char == self.EOF:
#             return False
#         if char in valid:
#             return True
#         self.backup()
#         return False
#
#     def accept_run(self, valid: str = None) -> None:
#         if valid is None: raise NotImplementedError
#         while True:
#             char = self.next()
#             if char == self.EOF:
#                 return
#             if char not in valid:
#                 break
#         self.backup()
#
#     def emit(self, type_: Enum = None) -> None:
#         self._items.append(LexerItemModel(
#             type=type_,
#             text=self._source[self._start: self._pos],
#             start=self._start,
#             pos=self._pos,
#         ))
#         self._start = self._pos
#
#     def error(self, type_: Enum = None, message: str = None) -> None:
#         self._items.append(LexerItemModel(
#             type=type_,
#             message=message,
#             text=self._source[self._start: self._pos],
#             start=self._start,
#             pos=self._pos,
#         ))
#
#     """ Properties """
#
#     @property
#     def source(self) -> str:
#         return self._source
#
#     @property
#     def initial(self) -> State:
#         return self._initial
#
#     @property
#     def state(self) -> State:
#         return self._state
#
#     @state.setter
#     def state(self, state: State) -> None:
#         self._state = state
#
#     @property
#     def start(self) -> int:
#         return self._start
#
#     @start.setter
#     def start(self, start: int) -> None:
#         self._start = start
#
#     @property
#     def pos(self) -> int:
#         return self._pos
#
#     @pos.setter
#     def pos(self, pos: int) -> None:
#         self._pos = pos
#
#     @property
#     def depth(self) -> int:
#         return self._depth
#
#     @depth.setter
#     def depth(self, depth: int) -> None:
#         self._depth = depth
#
#     @property
#     def items(self) -> list[LexerItemModel]:
#         return self._items
#
#     @items.setter
#     def items(self, items: list[LexerItemModel]) -> None:
#         self._items = items
#
#     @property
#     def data(self) -> LexerDataModel:
#         return self._data
#
#     @data.setter
#     def data(self, data: LexerDataModel) -> None:
#         self._data = data
#
#
# __all__ = [
#     "Lexer",
# ]
