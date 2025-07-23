"""
1. Twine
1.1. 获取文件绝对路径 (按文件进行一级分割)
1.2. 获取段落信息 (按段落进行二级分割)
1.3. 获取基础元素信息 (comment, head, macro, tag, script, 剩下的就是 plain text)
1.4. ？将元素组合？
1.5. 修改为可导入 paratranz 的格式
1.6. 导出为 json 文件
"""
import shutil
from contextlib import suppress

import ujson as json
import os
import re
from enum import Enum
from pathlib import Path

from src import GameRootNotExistException
from src.config import DIR_DOL, DIR_DATA
from src.log import logger


class Patterns(Enum):
    """Regexes"""
    PASSAGE_HEAD = re.compile(r""":: ?([\-\w.\'\"/& ]+) ?(\[[\S ]+])?\n""")
    COMMENT = re.compile(r"""(?:/\*|<!--)[\s\S]+?(?:\*/|-->)""")
    MACRO = re.compile(r"""<</?([\w=\-]+)(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")
    TAG = re.compile(r"""(?<!<)<(?![<!])/?(\w+)\s*[\s\S]*?(?<!>)>(?!>)""")

    """ SPECIAL """
    MACRO_WIDGET = re.compile(r"""<<widget(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")

class Parser:
    def __init__(self, game_root: Path = DIR_DOL):
        self._game_root: Path = game_root       # 需要汉化的游戏内容根目录，默认 DoL | Root path for the game needed to be localized, DoL as default
        self._all_filepaths: list[Path] = []    # 所有文件绝对路径 | Absolute paths for all the files
        logger.debug(f"Game root: {self._game_root}")

    @staticmethod
    def clean(*filepaths: Path):
        for fp in filepaths:
            with suppress(FileNotFoundError):
                shutil.rmtree(fp)
            os.makedirs(fp, exist_ok=True)

    def get_all_filepaths(self) -> list[Path]:
        raise NotImplementedError

    @property
    def game_root(self) -> Path:
        return self._game_root

    @property
    def all_filepaths(self) -> list[Path]:
        return self._all_filepaths

    @all_filepaths.setter
    def all_filepaths(self, fps: list[Path]) -> None:
        self._all_filepaths = fps


class TwineParser(Parser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._all_passages: list[dict[str, str]] | None = None
        self._all_passages_by_passage: dict[str, dict[str, str]] | None = None

        self._all_elements: list[dict[str, str]] | None = None
        self._all_elements_by_passage: dict[str, list[dict[str, str]]] | None = None

    def get_all_filepaths(self) -> list[Path]:
        if not self.game_root.exists():
            raise GameRootNotExistException

        self.all_filepaths = [
            Path(root) / file
            for root, dirs, files in os.walk(self.game_root)
            for file in files
            if file.endswith(".twee")
        ]
        return self.all_filepaths

    def get_all_passages_info(self) -> list[dict[str, str]]:
        all_passages = []
        all_passages_by_passage = {}
        for filepath in self.all_filepaths:
            filepath_relative = filepath.relative_to(self.game_root)
            with open(filepath, "r", encoding="utf-8") as fp:
                content = fp.read()

            # Some files are blank
            if not content:
                continue

            # 按照段落标题的标识符分割
            # 得到每段(标题+主体)
            # 手动加个换行方便分割
            content = f"\n{content}"
            # 以每个段落标题前一位置的换行作为分割符
            split_pattern = re.compile(rf"\n(?={Patterns.PASSAGE_HEAD.value.pattern})")

            # 格式：[空字符串, (段落名, 方括号标签, 花括号标签, 段落全文), (...), ...]
            passages = re.split(split_pattern, content)[1:]
            passage_titles = passages[::3]  # 段落名
            passage_tags = passages[1::3]   # 方括号标签
            passage_fulls = passages[2::3]  # 段落全文
            passage_texts = [
                re.sub(re.compile(rf"^{Patterns.PASSAGE_HEAD.value.pattern}"), "", full)
                for full in passage_fulls
            ]  # 段落主体

            all_passages_part = []
            for idx, passage_full in enumerate(passage_fulls):
                tag = passage_tags[idx].strip("[]") if passage_tags[idx] else None
                passage_data = {
                    "filepath": filepath_relative.__str__(),
                    "passage_title": passage_titles[idx].strip(),
                    "passage_tag": tag,
                    "passage_text": passage_texts[idx],
                    "length": len(passage_texts[idx])
                }

                if tag == "widget":
                    passage_data["widgets"] = self._split_widgets(passage_texts[idx])
                all_passages_part.append(passage_data)

            all_passages.extend(all_passages_part)

        os.makedirs(DIR_DATA, exist_ok=True)
        with open(DIR_DATA / "all_passages.json", "w", encoding="utf-8") as fp:
            json.dump(all_passages, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        all_passages_by_passage = {
            passage_data["passage_title"]: passage_data
            for passage_data in all_passages
        }
        with open(DIR_DATA / "all_passages_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(all_passages_by_passage, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        self.all_passages = all_passages
        self.all_passages_by_passage = all_passages_by_passage

        max_length_only_passage = max([p['length'] for p in all_passages])
        min_length_only_passage = min([p['length'] for p in all_passages])
        max_length_only_passage_title = list(filter(lambda p: p['length'] == max_length_only_passage, all_passages))[0]['passage_title']
        min_length_only_passage_title = list(filter(lambda p: p['length'] == min_length_only_passage, all_passages))[0]['passage_title']

        pairs = {}
        for passage in all_passages:
            if "widgets" not in passage:
                pairs[passage["passage_title"]] = passage["length"]
            else:
                for widget in passage["widgets"]:
                    pairs[widget["widget_name"]] = widget["length"]
        max_length_with_widget = max(pairs.values())
        min_length_with_widget = min(pairs.values())
        max_length_with_widget_title = {v: k for k, v in pairs.items()}[max_length_with_widget]
        min_length_with_widget_title = {v: k for k, v in pairs.items()}[min_length_with_widget]

        logger.debug(f"passages: {len(all_passages)}")
        logger.debug(f"maximum length (only passage): {max_length_only_passage}")
        logger.debug(f"maximum length passage (only passage): {max_length_only_passage_title}")
        logger.debug(f"minimum length (only passage): {min_length_only_passage}")
        logger.debug(f"minimum length passage (only passage): {min_length_only_passage_title}")

        logger.debug(f"maximum length (with widget): {max_length_with_widget}")
        logger.debug(f"maximum length passage (with widget): {max_length_with_widget_title}")
        logger.debug(f"minimum length (with widget): {min_length_with_widget}")
        logger.debug(f"minimum length passage (with widget): {min_length_with_widget_title}")

        return all_passages

    def get_all_elements_info(self) -> list[dict[str, str]]:
        all_elements = []
        for passage in self.all_passages:
            filepath = passage["filepath"]
            title = passage["passage_title"]
            content = passage["passage_text"]

            all_elements_part = []
            flag = False
            for pattern in {Patterns.COMMENT, Patterns.MACRO, Patterns.TAG}:
                for match in re.finditer(pattern.value, content):
                    flag = True
                    all_elements_part.append({
                        "filepath": filepath,
                        "passage_title": title,
                        "type": pattern.name,
                        "element": match.group(),
                        "pos_start": match.start(),
                        "pos_end": match.end(),
                        "length": match.end() - match.start()
                    })

            if not flag:  # 只有纯文本
                all_elements_part.append({
                    "filepath": filepath,
                    "passage_title": title,
                    "type": "TEXT",
                    "element": content,
                    "pos_start": 0,
                    "pos_end": len(content),
                    "length": len(content)
                })

            all_elements_part = self._sort_elements(all_elements_part)
            all_elements_part = self._filter_elements_inside_another(all_elements_part)
            all_elements_part = self._fill_plaintexts(all_elements_part, filepath, content, title)
            all_elements.extend(all_elements_part)

        with open(DIR_DATA / "all_elements.json", "w", encoding="utf-8") as fp:
            json.dump(all_elements, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        all_elements_by_passage = {}
        for idx, element in enumerate(all_elements):
            if element["passage_title"] not in all_elements_by_passage:
                all_elements_by_passage[element["passage_title"]] = [element]
            else:
                all_elements_by_passage[element["passage_title"]].append(element)
        with open(DIR_DATA / "all_elements_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(all_elements_by_passage, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        self.all_elements = all_elements
        self.all_elements_by_passage = all_elements_by_passage

        logger.debug(f"elements: {len(all_elements)}")
        logger.debug(f"maximum length: {max([_['length'] for _ in all_elements])}")
        logger.debug(f"minimum length: {min([_['length'] for _ in all_elements])}")
        return all_elements

    """ UTILITY FUNCTIONS """
    @staticmethod
    def _split_widgets(passage_text: str) -> list:
        widget_pattern = re.compile(rf"""{Patterns.MACRO_WIDGET.value.pattern}([\s\S]*?)<</widget>>""")
        result = []
        for match in re.finditer(widget_pattern, passage_text):
            widget_name, widget_text = match.groups()
            widget_name_pure = re.findall(r"\"(\S+)\"", widget_name)
            widget_name = widget_name_pure[0] if widget_name_pure else widget_name

            result.append({
                "widget_name": widget_name,
                "widget_text": widget_text,
                "widget_pos_start": match.start(),
                "widget_pos_end": match.end(),
                "length": len(widget_text),
            })
        return result

    @staticmethod
    def _sort_elements(elements: list[dict[str, str]]) -> list[dict[str, str]]:
        return sorted(elements, key=lambda elem: elem["pos_start"])

    @staticmethod
    def _filter_elements_inside_another(elements: list[dict[str, str] | None]) -> list[dict[str, str]]:
        """因为按照正则提取，有些在某一元素里的另一元素被当做独立元素抓出来了，把这部分内容去掉"""
        elements_copy = elements.copy()
        for idx, element in enumerate(elements_copy):
            for i in range(len(elements_copy) - idx):
                if i == 0:
                    continue
                # 因为按照 pos_start 排序过了，所以被包裹住的元素开头一定在当前元素开头的后面
                # 因此当出现后者开头小于当前元素结尾时，后者是被当前元素包裹住的元素
                if elements_copy[idx+i]["pos_start"] < element["pos_end"]:
                    elements[idx+i] = None

        return list(filter(lambda _: _ is not None, elements))

    @staticmethod
    def _fill_plaintexts(elements: list[dict[str, str | int]], filepath: str, content: str, title: str) -> list[dict[str, str]]:
        """经过处理后，夹在两个元素之间的就是纯文本"""
        elements_copy = elements.copy()
        for idx, element in enumerate(elements_copy):
            # 向前判断一次
            # 在开头之前可能有纯文本
            if idx == 0 < element["pos_start"]:
                text = content[:element["pos_start"]]
                pos_start = 0
                pos_end = element["pos_start"]
                elements.append({
                    "filepath": filepath,
                    "passage_title": title,
                    "type": "TEXT",
                    "element": text,
                    "pos_start": pos_start,
                    "pos_end": pos_end,
                    "length": pos_end - pos_start
                })

            # 向后判断一次
            # 非开头 非末尾
            if idx < len(elements_copy) - 1:
                # 前后两元素中间没有内容
                if element["pos_end"] == elements_copy[idx + 1]["pos_start"]:
                    continue

                text = content[element["pos_end"]:elements_copy[idx + 1]["pos_start"]]
                pos_start = element["pos_end"]
                pos_end = elements_copy[idx + 1]["pos_start"]

            # 在末尾之后可能有纯文本
            else:
                # 元素末尾就是段落末尾
                if element["pos_end"] >= len(content):
                    continue

                text = content[element["pos_end"]:]
                pos_start = element["pos_end"]
                pos_end = len(content)

            elements.append({
                "filepath": filepath,
                "passage_title": title,
                "type": "TEXT",
                "element": text,
                "pos_start": pos_start,
                "pos_end": pos_end,
                "length": pos_end - pos_start
            })
        return TwineParser._sort_elements(elements)

    """ GETTER & SETTER """
    @property
    def all_passages(self) -> list[dict[str, str]]:
        return self._all_passages

    @all_passages.setter
    def all_passages(self, passages: list[dict[str, str]]) -> None:
        self._all_passages = passages

    @property
    def all_passages_by_passage(self) -> dict[str, dict[str, str]]:
        return self._all_passages_by_passage

    @all_passages_by_passage.setter
    def all_passages_by_passage(self, passages_by_passage: dict[str, dict[str, str]]) -> None:
        self._all_passages_by_passage = passages_by_passage

    @property
    def all_elements_by_passage(self) -> dict[str, list[dict[str, str]]]:
        return self._all_elements_by_passage

    @all_elements_by_passage.setter
    def all_elements_by_passage(self, elements_by_passage: dict[str, list[dict[str, str]]]) -> None:
        self._all_elements_by_passage = elements_by_passage

    @property
    def all_elements(self) -> list[dict[str, str]]:
        return self._all_elements

    @all_elements.setter
    def all_elements(self, elements: list[dict[str, str]]) -> None:
        self._all_elements = elements


class JavaScriptParser(Parser):
    def get_all_filepaths(self) -> list[Path]:
        return [
            Path(root) / file
            for root, dirs, files in os.walk(self.game_root)
            for file in files
            if file.endswith(".js")
        ]


if __name__ == '__main__':
    parser = TwineParser(
        # game_root=DIR_DOLP
        game_root=DIR_DOL
    )
    paths = parser.get_all_filepaths()
    parser.get_all_passages_info()
    parser.get_all_elements_info()
