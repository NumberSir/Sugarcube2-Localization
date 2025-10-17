# import re
#
# from src.core.schema.enum import Patterns
#
# class MacroParser:
#     def __init__(self):
#         self._name: str = "macro"
#         self._profiles: list[str] = ["core"]
#         self._match: str = "<<"
#         self._lookahead: re.Pattern = Patterns.Macro
#         self._working: dict = {
#             "source": "",
#             "name": "",
#             "arguments": "",
#             "index": 0
#         }
#         self._context = None
#
