"""
标题 --- :: ?([\S ]+)\s?(\[[\S ]+])?\s?(\{[\s\S]+})?
1. Twine
1.1. 获取文件绝对路径 (按文件进行一级分割)
1.2. 获取段落信息 (按段落进行二级分割)
1.3. 获取基础元素信息 (comment, head, macro, tag, script, 剩下的就是 plain text)
1.4. 将成对元素初次组合 (按基础元素进行四级分割)
1.5. 按照字数二次组合 (按字数进行三级分割)
1.6. 修改为可导入 paratranz 的格式
1.7. 导出为 json 文件
"""
import ujson as json
import os
import re
from enum import Enum
from pathlib import Path

from src.config import settings, DefaultGames
from src.log import logger


class Patterns(Enum):
    """正则"""
    PASSAGE_HEAD = re.compile(r""":: ?([\-\w.\'\"/& ]+) ?(\[[\S ]+])?\n""")
    COMMENT = re.compile(r"""(?:/\*|<!--)[\s\S]+?(?:\*/|-->)""")
    MACRO = re.compile(r"""<</?([\w=\-]+)(?:\s+((?:(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)|(?://.*\n)|(?:`(?:\\.|[^`\\\n])*?`)|(?:"(?:\\.|[^"\\\n])*?")|(?:'(?:\\.|[^'\\\n])*?')|(?:\[(?:[<>]?[Ii][Mm][Gg])?\[[^\r\n]*?]]+)|[^>]|(?:>(?!>)))*?))?>>""")
    TAG = re.compile(r"""(?<!<)<(?![<!])/?(\w+)\s*[\s\S]*?(?<!>)>(?!>)""")


class Parser:
    def __init__(self, game_root: Path = settings.file.root / settings.file.repo / DefaultGames.degrees_of_lewdity.value):
        self._game_root: Path = game_root       # 需要汉化的游戏内容根目录，默认 DoL
        self._all_filepaths: list[Path] = []    # 所有文件绝对路径

    def get_all_filepaths(self) -> list[Path]:
        """获取所有需要提取的文件绝对路径"""
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

        self._all_passages: list[dict[str, str]] | None = None # 段落信息
        self._all_elements: list[dict[str, str]] | None = None # 基本元素信息

    def get_all_filepaths(self) -> list[Path]:
        self.all_filepaths = [
            Path(root) / file
            for root, dirs, files in os.walk(self.game_root)
            for file in files
            if file.endswith(".twee")
        ]
        return self.all_filepaths

    def get_all_passages_info(self) -> list[dict[str, str]]:
        """获取所有段落信息"""
        result = []
        for filepath in self.all_filepaths:
            filepath_relative = filepath.relative_to(self.game_root)
            with open(filepath, "r", encoding="utf-8") as fp:
                content = fp.read()

            # 有些文件为空
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

            passage_data = [
                {
                    "filepath": filepath_relative.__str__(),
                    "passage_title": passage_titles[idx].strip(),
                    "passage_tag": passage_tags[idx].strip("[]") if passage_tags[idx] else None,
                    "passage_text": passage_texts[idx]
                }
                for idx, _ in enumerate(passage_fulls)
            ]
            result.extend(passage_data)

        logger.debug(f"passages count: {len(result)}")
        with open(settings.file.root / settings.file.data / "all_passages.json", "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        self.all_passages = result
        return result

    def get_all_elements_info(self) -> list[dict[str, str]]:
        """获取所有基础元素信息"""
        result = []
        for passage in self.all_passages:
            filepath = passage["filepath"]
            title = passage["passage_title"]
            content = passage["passage_text"]

            elements = []
            flag = False
            for pattern in {Patterns.COMMENT, Patterns.MACRO, Patterns.TAG}:
                for match in re.finditer(pattern.value, content):
                    flag = True
                    elements.append({
                        "filepath": filepath,
                        "passage_title": title,
                        "type": pattern.name,
                        "element": match.group(),
                        "pos_start": match.start(),
                        "pos_end": match.end()
                    })

            if not flag:  # 只有纯文本
                elements.append({
                    "filepath": filepath,
                    "passage_title": title,
                    "type": "TEXT",
                    "element": content,
                    "pos_start": 0,
                    "pos_end": len(content)
                })

            elements = self._sort_elements(elements)
            elements = self._filter_comment_inside(elements)
            elements = self._fill_plaintexts(elements, filepath, content, title)
            result.extend(elements)

        with open(settings.file.root / settings.file.data / "all_elements.json", "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        logger.debug(f"elements count: {len(result)}")
        self.all_elements = result
        return result

    @staticmethod
    def _sort_elements(elements: list[dict[str, str]]) -> list[dict[str, str]]:
        """按照位置顺序排列元素"""
        return sorted(elements, key=lambda elem: elem["pos_start"])

    @staticmethod
    def _filter_comment_inside(elements: list[dict[str, str] | None]) -> list[dict[str, str]]:
        """因为按照正则提取，有些在注释里的内容也被抓出来了，把这部分内容去掉"""
        elements_copy = elements.copy()
        for idx, element in enumerate(elements_copy):
            if element["type"] != Patterns.COMMENT.name:
                continue

            for i in range(len(elements_copy) - idx):
                if i == 0:
                    continue

                # 因为按照 pos_start 排序过了，所以被注释包裹的元素一定在注释的后面
                # 因此当出现后者开头小于前者结尾时一定是前者是注释，而后者是被注释包住的元素
                if elements_copy[idx + i]["pos_start"] < element["pos_end"]:
                    elements[idx + i] = None

        return [_ for _ in elements if _ is not None]

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
            })
        return TwineParser._sort_elements(elements)

    @property
    def all_passages(self) -> list[dict[str, str]]:
        return self._all_passages

    @all_passages.setter
    def all_passages(self, passages: list[dict[str, str]]) -> None:
        self._all_passages = passages

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
        # game_root=settings.file.root / settings.file.repo / DefaultGames.degrees_of_lewdity_plus.value
        game_root=settings.file.root / settings.file.repo / DefaultGames.degrees_of_lewdity.value
    )
    paths = parser.get_all_filepaths()
    parser.get_all_passages_info()
    parser.get_all_elements_info()
