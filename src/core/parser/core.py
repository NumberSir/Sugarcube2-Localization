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


class Patterns(Enum):
    """正则"""
    """段落头   :: <段落名> <[标签]>"""
    TWINE_PASSAGE_HEAD = re.compile(r":: ?([\-\w.\'\"/& ]+)\s?(\[[\S ]+])?")


class Parser:
    def __init__(self, game_root: Path = settings.file.root / settings.file.repo / DefaultGames.degrees_of_lewdity.value):
        self._game_root: Path = game_root  # 需要汉化的游戏内容根目录，默认 DoL

        self._all_filepaths: list[Path] = []  # 所有文件绝对路径

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


    def get_all_filepaths(self) -> list[Path]:
        self.all_filepaths = [
            Path(root) / file
            for root, dirs, files in os.walk(self.game_root)
            for file in files
            if file.endswith(".twee")
        ]
        return self.all_filepaths

    def get_all_passages_info(self):
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
            split_pattern = re.compile(fr"\n(?={Patterns.TWINE_PASSAGE_HEAD.value.pattern})")

            # 格式：[空字符串, (段落名, 方括号标签, 花括号标签, 段落全文), (...), ...]
            passages = re.split(split_pattern, content)[1:]
            passage_names = passages[::3]   # 段落名
            passage_tags = passages[1::3]  # 方括号标签
            passage_fulls = passages[2::3]  # 段落全文
            passage_bodys = [
                re.sub(re.compile(rf"^{Patterns.TWINE_PASSAGE_HEAD.value.pattern}"), "", full)
                for full in passage_fulls
            ]  # 段落主体

            passage_data = [
                {
                    "filepath": filepath_relative.__str__(),
                    "passage_tag": passage_tags[idx].strip("[]") if passage_tags[idx] else None,
                    "passage_name": passage_names[idx].strip(),
                    "passage_body": passage_bodys[idx].strip()
                }
                for idx, _ in enumerate(passage_fulls)
            ]
            result.extend(passage_data)

        with open(settings.file.root / settings.file.data / "all_passages.json", "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2)

        print(len(result))
        return result


class JavaScriptParser(Parser):
    def get_all_filepaths(self) -> list[Path]:
        return [
            Path(root) / file
            for root, dirs, files in os.walk(self.game_root)
            for file in files
            if file.endswith(".js")
        ]


if __name__ == '__main__':
    from pprint import pprint
    parser = TwineParser()
    paths = parser.get_all_filepaths()
    parser.get_all_passages_info()
