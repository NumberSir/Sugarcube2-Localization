"""
Split twinescript (.twee / .tw) into basic elements:
Twinescript File
┗━ Passages
   ┣━ Passage Head: `:: PASSAGE HEAD`
   ┗━ Passage Body
      ┗━ is passage widget?
         ┣━ √
         ┃  ┣━ Widget Head: `<<widget "NAME" ARGS*>>`
         ┃  ┣━ Elements
         ┃  ┗━ Widget Tail: `<</widget>>`
         ┗━ ×
            ┗━ Elements
               ┣━ Comment:      `<!-- HTML style -->` | `/* C style */` | `/% TiddlyWiki style %/`
               ┣━ Macro:        `<<MACRO>>`
               ┣━ Tag:          `<TAG>`
               ┣━ Script:       `<script> JAVASCRIPT </script>`
               ┗━ Plain Text:   except of any elements above
"""

import os
import re
from typing_extensions import deprecated

import ujson as json

from pathlib import Path
from typing import Iterator

from src.config import DIR_DATA
from src.exceptions import GameRootNotExistException
from src.log import logger
from src.core.utils import get_all_filepaths
from src.core.parser.internal import Parser
from src.core.schema.enum import Patterns, Mappings
from src.core.schema.model import (
    WidgetModel, PassageModel, ElementModel,
    ElementCommentModel, ElementMacroModel, ElementTagModel, ElementTextModel, ElementVariableModel
)


class TwineParser(Parser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        """All filepaths with suffix '.twee'"""
        self._all_filepaths: list[Path] = None

        """All passages' info: title, tag, body, position, length and widgets contained."""
        self._all_passages: list[PassageModel] | None = None
        """Same as above, indexed by passage title."""
        self._all_passages_by_passage: dict[str, PassageModel] | None = None

        """All elements' info: type, body, position and length."""
        self._all_elements: list[ElementModel] | None = None
        """Same as above, indexed by passage title."""
        self._all_elements_by_passage: dict[str, list[ElementModel]] | None = None

    def get_all_filepaths(self) -> Iterator[Path]:
        """Get all twinescript absolute filepaths."""
        if not self.game_root.exists():
            raise GameRootNotExistException
        self.all_filepaths = get_all_filepaths(".twee", self.game_root)
        return self.all_filepaths

    def get_all_passages_info(self) -> tuple[list[PassageModel], dict[str, PassageModel]]:
        """Get all passages' info from twinescript files."""
        all_passages: list[PassageModel] = []
        all_filepaths = self.all_filepaths or self.get_all_filepaths()
        for filepath in all_filepaths:
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

            # 格式：[空字符串, (段落名, 方括号标签, 花括号数据, 段落全文), (...), ...]

            passages = re.split(split_pattern, content)[1:]
            passage_titles = passages[::5]  # 段落名
            passage_tags = passages[1::5]   # 方括号标签
            passage_tags = [_.strip().strip("[").strip("]") if _ is not None else _ for _ in passage_tags]
            passage_datas = passages[3::5]  # 花括号数据
            passage_fulls = passages[4::5]  # 段落全文
            passage_bodys = [
                re.sub(re.compile(rf"^{Patterns.PASSAGE_HEAD.value.pattern}"), "", full)
                for full in passage_fulls
            ]  # 段落主体

            all_passages_part = []
            for idx, passage_full in enumerate(passage_fulls):
                tag = passage_tags[idx].strip("[]") if passage_tags[idx] else None
                all_passages_part.append(PassageModel(
                    filepath=filepath,
                    title=passage_titles[idx].strip(),
                    tag=tag,
                    body=passage_bodys[idx],
                    length=len(passage_bodys[idx]),
                    widgets=self._split_widgets(passage_bodys[idx]) if tag == "widget" else None,
                ))
            all_passages.extend(all_passages_part)

        """ Temporarily saved. """
        os.makedirs(DIR_DATA, exist_ok=True)
        with open(DIR_DATA / "all_passages.json", "w", encoding="utf-8") as fp:
            json.dump(
                [_.model_dump(mode="json") for _ in all_passages],
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

        all_passages_by_passage = {
            passage_model.title: passage_model
            for passage_model in all_passages
        }
        with open(DIR_DATA / "all_passages_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(
                {k: v.model_dump(mode="json") for k, v in all_passages_by_passage.items()},
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

        self.all_passages = all_passages
        self.all_passages_by_passage = all_passages_by_passage
        logger.success(f"{len(self.all_passages)} passages found.")

        """ Debug texts, no actual use."""
        max_length_only_passage = max([p.length for p in all_passages])
        min_length_only_passage = min([p.length for p in all_passages])
        max_length_only_passage_title = list(filter(lambda p: p.length == max_length_only_passage, all_passages))[0].title
        min_length_only_passage_title = list(filter(lambda p: p.length == min_length_only_passage, all_passages))[0].title

        pairs: dict[str, int] = {}
        for passage in all_passages:
            if passage.widgets:
                for widget in passage.widgets:
                    pairs[widget.name] = widget.length
            else:
                pairs[passage.title] = passage.length
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

        return all_passages, all_passages_by_passage

    def get_all_elements_info(self) -> tuple[list[ElementModel], dict[str, list[ElementModel]]]:
        """Split each passage into basic elements."""
        all_elements: list[ElementModel] = []
        all_passages = self.all_passages or self.get_all_passages_info()[0]

        for passage in all_passages:
            filepath = passage.filepath
            title = passage.title
            body = passage.body

            all_elements_part: list[ElementModel] = []
            flag = False
            """Elements have clear definition."""
            for pattern in {Patterns.COMMENT, Patterns.MACRO, Patterns.TAG}:
                for match in re.finditer(pattern.value, body):
                    flag = True
                    all_elements_part.append(ElementModel(
                        filepath=filepath,
                        title=title,
                        type=pattern.name,
                        body=match.group(),
                        pos_start=match.start(),
                        pos_end=match.end(),
                        length=match.end() - match.start(),
                    ))

            if not flag:  # Only plain text
                all_elements_part.append(ElementModel(
                    filepath=filepath,
                    title=title,
                    type=Patterns.TEXT.name,
                    body=body,
                    pos_start=0,
                    pos_end=len(body),
                    length=len(body),
                ))

            all_elements_part = self._sort_elements(all_elements_part)
            all_elements_part = self._filter_elements_inside_another(all_elements_part)
            all_elements_part = self._fill_plaintexts(all_elements_part, filepath, body, title)
            all_elements_part = self._merge_elements_inside_script(all_elements_part)
            all_elements.extend(all_elements_part)

        with open(DIR_DATA / "all_elements.json", "w", encoding="utf-8") as fp:
            json.dump(
                [_.model_dump(mode="json") for _ in all_elements],
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

        all_elements_by_passage: dict[str, list[ElementModel]] = {}
        for idx, element in enumerate(all_elements):
            if element.title not in all_elements_by_passage:
                all_elements_by_passage[element.title] = [element]
            else:
                all_elements_by_passage[element.title].append(element)
        with open(DIR_DATA / "all_elements_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(
                {k: [v.model_dump(mode="json") for v in vs] for k, vs in all_elements_by_passage.items()},
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

        self.all_elements = all_elements
        self.all_elements_by_passage = all_elements_by_passage
        logger.success(f"{len(self.all_elements)} elements found.")

        """Debug texts, no actual use."""
        logger.debug(f"elements: {len(all_elements)}")
        logger.debug(f"maximum length: {max([_.length for _ in all_elements])}")
        logger.debug(f"minimum length: {min([_.length for _ in all_elements])}")
        return all_elements, all_elements_by_passage

    def get_all_elements_info_detailed(self) -> list[ElementModel]:
        all_elements_by_passage = self.all_elements_by_passage or self.get_all_elements_info()[1]
        all_elements_by_passage_detailed = all_elements_by_passage.copy()

        for passage, elements in all_elements_by_passage.items():
            element_level = 0
            for idx, element in enumerate(elements):
                match element.type:
                    case Patterns.COMMENT.name:
                        """ /* content */ """
                        content = re.match(Patterns.COMMENT.value, element.body).groups()[0]
                        element.data = ElementCommentModel(content=content)
                    case Patterns.MACRO.name:
                        """ <<name args>> """
                        # TODO
                        name, args = re.match(Patterns.MACRO.value, element.body).groups()
                        args_desugared = self.desugar(args) if args else None
                        element.body_desugared = f"<<{name} {args_desugared}>>" if args else element.body
                        if is_close := name.startswith("/"):
                            name = name.lstrip("/")
                        element.data = ElementMacroModel(name=name, args=args, is_close=is_close)
                    case Patterns.TAG.name:
                        """<name args>"""
                        # TODO
                        name, args = re.match(Patterns.MACRO.value, element.body).groups()
                        if is_close := name.startswith("/"):
                            name = name.lstrip("/")
                        element.data = ElementTagModel(name=name, args=args, is_close=is_close)
                    case Patterns.TEXT.name:
                        # TODO
                        if element.body.startswith("$") or element.body.startswith("_"):
                            display_name = element.body
                            element.data = ElementVariableModel(display_name=display_name)
                        else:
                            element.data = ElementVariableModel()
                    case _:
                        raise TypeError(f"Unknown element type: {element.type}")

                element.level = element_level
                all_elements_by_passage_detailed[passage][idx] = element

        all_elements_detailed = []
        for passage, elements in all_elements_by_passage_detailed.items():
            all_elements_detailed.extend(elements)

        with open(DIR_DATA / "all_elements_detailed.json", "w", encoding="utf-8") as fp:
            json.dump(
                [_.model_dump(mode="json") for _ in all_elements_detailed],
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

        with open(DIR_DATA / "all_elements_by_passage_detailed.json", "w", encoding="utf-8") as fp:
            json.dump(
                {k: [v.model_dump(mode="json") for v in vs] for k, vs in all_elements_by_passage_detailed.items()},
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

    """ Restore TwineScript to JavaScript """
    # TODO: Optimization
    def restore_javascript(self):
        all_passages = self.all_passages or self.get_all_passages_info()[0]
        for idx, passage in enumerate(all_passages):
            logger.info(f"Restoring passage {idx}/{len(all_passages)}: {passage.title}")
            all_passages[idx].body = self.desugar(passage.body)

        with open(DIR_DATA / "all_passages_desugared.json", "w", encoding="utf-8") as fp:
            json.dump(
                [_.model_dump(mode="json") for _ in all_passages],
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

        all_passages_by_passage = {
            passage_model.title: passage_model
            for passage_model in all_passages
        }
        with open(DIR_DATA / "all_passages_by_passage_desugared.json", "w", encoding="utf-8") as fp:
            json.dump(
                {k: v.model_dump(mode="json") for k, v in all_passages_by_passage.items()},
                fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
            )

    def desugar(self, twinescript_code: str) -> str:
        """
        1. 变量: $ -> State.variables., ...
        2. 表达式: to -> ==, gte -> >=, ...
        """
        code = twinescript_code
        matches = list(re.finditer(Patterns.DESUGAR.value, code))

        """替换字符串后顺序坐标会改变，因此倒序替换"""
        """no-op: Empty quotes, Double quoted, Single quoted, Operator characters, Spread/rest syntax"""
        for idx, match in enumerate(matches[::-1]):
            # Template literal, non-empty.
            if sugared_template := match[1]:
                template = self.desugar_template(sugared_template)
                if template != sugared_template:
                    code = (
                        f"{code[:match.start()]}"
                        f"{template}"
                        f"{code[match.start()+len(sugared_template):]}"
                    )

            # Barewords.
            elif token := match[2]:
                # logger.info(f"match token: {idx}/{len(matches)} - {token}")
                """
                If the token is simply a dollar-sign or underscore, then it's either
                just the raw character or, probably, a function alias, so skip it.
                """
                if token in {'$', '_'}:
                    continue

                """
                If the token is a story $variable or temporary _variable, then reset
                it to just its sigil for replacement.
                """
                if re.match(Patterns.VARIABLE.value, token):
                    token = token[0]

                """    
                If the finalized token has a mapping, replace it within the code string
                with its counterpart.
                """
                if replacement := Mappings.TOKEN.value.get(token):
                    code = (
                        f"{code[:match.start()]}"
                        f"{replacement}"
                        f"{code[match.start()+len(token):]}"
                    )

        return code

    def desugar_template(self, twinescript_template: str) -> str:
        """ `...${content}...${...${nested_content}...}...` """
        template = twinescript_template

        start_match_search_pos = 0
        while start_match := Patterns.TEMPLATE_GROUP_START.value.search(template, pos=start_match_search_pos):
            depth = 1

            start_index = start_match.start() + 2
            end_index = start_index
            end_match_search_pos = start_index
            while end_match := Patterns.TEMPLATE_GROUP_PARSE.value.search(template, pos=end_match_search_pos):
                # logger.info("loop 2")
                if end_match[1]:  # open
                    depth += 1
                    logger.info(f"{depth=}, {end_match=}")
                elif end_match[2]:  # close
                    depth -= 1
                    logger.info(f"{depth=}, {end_match=}")

                if depth == 0:
                    end_index = end_match.start()
                    break
                end_match_search_pos = end_match.start() + 1

            start_match_search_pos = start_index
            if end_index > start_index:
                old = template[start_index:end_index]
                new = self.desugar(old)

                template = (
                    f"{template[:start_index]}"
                    f"{new}"
                    f"{template[start_index+len(old):]}"
                )
                start_match_search_pos += len(new) - len(old)
                continue

        return template

    """ Utility Methods """
    @staticmethod
    def _split_widgets(passage_body: str) -> list[WidgetModel]:
        """Split each widget in single widget-passage into parts."""
        widget_pattern = re.compile(rf"""{Patterns.MACRO_WIDGET.value.pattern}([\s\S]*?)<</widget>>""")
        result = []
        for match in re.finditer(widget_pattern, passage_body):
            widget_name, widget_body = match.groups()
            widget_name_pure = re.findall(r"\"(\S+)\"", widget_name)
            widget_name = widget_name_pure[0] if widget_name_pure else widget_name

            result.append(WidgetModel(
                name=widget_name,
                body=widget_body,
                pos_start=match.start(),
                pos_end=match.end(),
                length=len(widget_body)
            ))
        return result

    @staticmethod
    def _sort_elements(elements: list[ElementModel]) -> list[ElementModel]:
        """Sort elements based on position."""
        return sorted(elements, key=lambda elem: elem.pos_start)

    @staticmethod
    def _filter_elements_inside_another(elements: list[ElementModel | None]) -> list[ElementModel]:
        """因为按照正则提取，有些在某一元素里的另一元素被当做独立元素抓出来了，把这部分内容去掉"""
        elements_copy = elements.copy()
        for idx, element in enumerate(elements_copy):
            for i in range(len(elements_copy) - idx):
                if i == 0:
                    continue
                # 因为按照 pos_start 排序过了，所以被包裹住的元素开头一定在当前元素开头的后面
                # 因此当出现后者开头小于当前元素结尾时，后者是被当前元素包裹住的元素
                if elements_copy[idx+i].pos_start < element.pos_end:
                    elements[idx+i] = None

        return list(filter(lambda _: _ is not None, elements))

    @staticmethod
    def _fill_plaintexts(elements: list[ElementModel], filepath: Path, content: str, title: str) -> list[ElementModel]:
        """经过处理后，夹在两个元素之间的就是纯文本"""
        elements_copy = elements.copy()
        for idx, element in enumerate(elements_copy):
            """向前判断一次"""
            # 在开头之前可能有纯文本
            if idx == 0 < element.pos_start:
                text = content[:element.pos_start]
                pos_start = 0
                pos_end = element.pos_start
                elements.append(ElementModel(
                    filepath=filepath,
                    title=title,
                    type="TEXT",
                    body=text,
                    pos_start=pos_start,
                    pos_end=pos_end,
                    length=pos_end - pos_start,
                ))

            """向后判断一次"""
            # 非开头 非末尾
            if idx < len(elements_copy) - 1:
                # 前后两元素中间没有内容
                if element.pos_end == elements_copy[idx+1].pos_start:
                    continue

                text = content[element.pos_end:elements_copy[idx+1].pos_start]
                pos_start = element.pos_end
                pos_end = elements_copy[idx+1].pos_start

            # 在末尾之后可能有纯文本
            else:
                # 元素末尾就是段落末尾
                if element.pos_end >= len(content):
                    continue

                text = content[element.pos_end:]
                pos_start = element.pos_end
                pos_end = len(content)

            elements.append(ElementModel(
                filepath=filepath,
                title=title,
                type="TEXT",
                body=text,
                pos_start=pos_start,
                pos_end=pos_end,
                length=pos_end - pos_start,
            ))
        """Sort again, including plain-text elements"""
        return TwineParser._sort_elements(elements)

    @staticmethod
    def _merge_elements_inside_script(elements: list[ElementModel]) -> list[ElementModel]:
        """
        <<script>>...<</script>>
        之中的内容统一判断为 JAVASCRIPT
        """
        result: list[ElementModel] = []
        filepath = elements[0].filepath
        title = elements[0].title
        type_ = Patterns.JAVASCRIPT.name
        pos_start = -1
        body = ""

        inside = False
        for idx, element in enumerate(elements):
            if not inside:  # <<script>> ，及其它元素
                result.append(element)
            elif element.body == "<</script>>":
                inside = False
                result.append(ElementModel(
                    filepath=filepath,
                    title=title,
                    type=type_,
                    pos_start=pos_start,
                    pos_end=element.pos_start,
                    length=element.pos_start-pos_start,
                    body=body,
                ))
                logger.info(f"inside, {body=}")
                result.append(element)
                continue
            else:  # 二者之间的元素，以及 <</script>>
                body = f"{body}{element.body}"
                continue

            if element.body == "<<script>>":
                inside = True
                pos_start = element.pos_end
                body = ""
                continue

        return result

    """ Getters & Setters """
    @property
    def all_filepaths(self) -> list[Path]:
        return self._all_filepaths

    @all_filepaths.setter
    def all_filepaths(self, filepaths: list[Path]) -> None:
        self._all_filepaths = filepaths

    @property
    def all_passages(self) -> list[PassageModel]:
        return self._all_passages

    @all_passages.setter
    def all_passages(self, passages: list[PassageModel]) -> None:
        self._all_passages = passages

    @property
    def all_passages_by_passage(self) -> dict[str, PassageModel]:
        return self._all_passages_by_passage

    @all_passages_by_passage.setter
    def all_passages_by_passage(self, passages_by_passage: dict[str, PassageModel]) -> None:
        self._all_passages_by_passage = passages_by_passage

    @property
    def all_elements_by_passage(self) -> dict[str, list[ElementModel]]:
        return self._all_elements_by_passage

    @all_elements_by_passage.setter
    def all_elements_by_passage(self, elements_by_passage: dict[str, list[ElementModel]]) -> None:
        self._all_elements_by_passage = elements_by_passage

    @property
    def all_elements(self) -> list[ElementModel]:
        return self._all_elements

    @all_elements.setter
    def all_elements(self, elements: list[ElementModel]) -> None:
        self._all_elements = elements


__all__ = [
    "TwineParser"
]


if __name__ == '__main__':
    parser = TwineParser()
    parser.get_all_elements_info()
