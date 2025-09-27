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
               ┣━ Comment:          `<!-- HTML style -->` | `/* C style */` | `/% TiddlyWiki style %/`
               ┣━ Macro:            `<<MACRO>>`
               ┣━ Tag:              `<TAG>`
               ┣━ Script:           `<script> JAVASCRIPT </script>`
               ┣━ Naked Variable:   `_var` and `$var`
               ┗━ Plain Text:       except of any elements above
"""

import re

from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session
from typing import Iterator

from src.database import ENGINE
from src.exceptions import GameRootNotExistException
from src.log import logger

from src.core.utils import get_all_filepaths
from src.core.parser.internal import Parser
from src.core.schema.enum import ModelField, Patterns
from src.core.schema.data_model import WidgetModel, PassageModel, ElementModel
from src.core.schema.sql_model import BaseTable, PassageModelTable, ElementModelTable



class Twee3Parser(Parser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # FIXME
        BaseTable.metadata.drop_all(ENGINE)
        BaseTable.metadata.create_all(ENGINE)

        self._suffix = ".twee"

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

        """All closed macros (eg: if, for, ...)"""
        self._all_closed_macros_names: set[str] | None = None
        """All closed tags (eg: div, span, ...)"""
        self._all_closed_tags_names: set[str] | None = None

    """ Story """
    def get_all_filepaths(self) -> Iterator[Path]:
        """Get all twinescript absolute filepaths."""
        if not self.game_root.exists():
            logger.error(f"Game root does not exist: {self.game_root}")
            raise GameRootNotExistException
        self.all_filepaths = get_all_filepaths(self.suffix, self.game_root)
        return self.all_filepaths

    """ Passage """
    def get_all_passages_info(self) -> tuple[list[PassageModel], dict[str, PassageModel]]:
        """Get all passages' info from twinescript files."""
        all_passages: list[PassageModel] = []
        all_filepaths = self.all_filepaths or self.get_all_filepaths()
        # 以每个段落标题前一位置的换行作为分割符
        passage_head_pattern = re.compile(rf"\n(?={Patterns.PassageHead.value.pattern})")
        passage_head_strip_pattern = re.compile(rf"^{Patterns.PassageHead.value.pattern}")

        for filepath in all_filepaths:
            all_passages = self._get_passage_info(filepath, all_passages, passage_head_pattern, passage_head_strip_pattern)

        if not all_passages:
            self.all_passages = []
            # self.all_passages_by_passage = {}
            logger.warning("0 passages found x-x.")
            return [], {}

        """ Temporarily saved. """
        with Session(ENGINE) as session:
            session.add_all(
                PassageModelTable(
                    filepath=passage_model.filepath.relative_to(self.game_root).__str__(),
                    title=passage_model.title,
                    tag=passage_model.tag,
                    body=passage_model.body,
                    length=passage_model.length,
                    widgets=[_.model_dump(mode="json") for _ in passage_model.widgets],
                )
                for passage_model in all_passages
            )
            session.commit()

        all_passages_by_passage = {
            passage_model.title: passage_model
            for passage_model in all_passages
        }

        self.all_passages = all_passages
        self.all_passages_by_passage = all_passages_by_passage
        logger.success(f"{len(self.all_passages)} passages found.")

        def _debug_output():
            """ Debug texts, no actual use."""
            max_length_only_passage = max(p.length for p in all_passages)
            min_length_only_passage = min(p.length for p in all_passages)
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

            logger.debug(f"maximum length (only passage): {max_length_only_passage}")
            logger.debug(f"maximum length passage (only passage): {max_length_only_passage_title}")
            logger.debug(f"minimum length (only passage): {min_length_only_passage}")
            logger.debug(f"minimum length passage (only passage): {min_length_only_passage_title}")

            logger.debug(f"maximum length (with widget): {max_length_with_widget}")
            logger.debug(f"maximum length passage (with widget): {max_length_with_widget_title}")
            logger.debug(f"minimum length (with widget): {min_length_with_widget}")
            logger.debug(f"minimum length passage (with widget): {min_length_with_widget_title}")

        _debug_output()
        return all_passages, all_passages_by_passage

    def _get_passage_info(self, filepath: Path, all_passages: list[PassageModel], passage_head_pattern: re.Pattern, passage_head_strip_pattern: re.Pattern) -> list[PassageModel]:
        with open(filepath, "r", encoding="utf-8") as fp:
            content = fp.read()

        # Some files are blank
        if not content:
            return all_passages

        # 按照段落标题的标识符分割
        # 得到每段(标题+主体)
        # 手动加个换行方便分割
        content = f"\n{content}"

        # 格式：[空字符串, (段落名, 方括号标签, 花括号数据, 换行，段落全文), (...), ...]
        passages = re.split(passage_head_pattern, content)[1:]
        if len(passages) % 5 != 0:
            logger.warning(f"File {filepath} has malformed passage structure, skipping.")
            return all_passages

        passage_names = passages[::5]  # 段落名
        passage_tags = [_.strip().strip("[").strip("]") if _ is not None else _ for _ in passages[1::5]]  # 方括号标签
        passage_metadatas = passages[3::5]  # 花括号数据
        passage_fulls = passages[4::5]  # 段落全文
        passage_bodys = [
            re.sub(passage_head_strip_pattern, "", full)
            for full in passage_fulls
        ]  # 段落主体

        for idx, passage_full in enumerate(passage_fulls):
            tag = passage_tags[idx] or ""
            widgets = self._split_widgets(passage_names[idx], passage_bodys[idx]) if tag == "widget" else []
            all_passages.append(PassageModel(
                filepath=filepath,
                title=passage_names[idx].strip(),
                tag=tag,
                body=passage_bodys[idx],
                length=len(passage_bodys[idx]),
                widgets=widgets,
            ))
        return all_passages

    """ Element """
    def get_all_elements_info(self) -> tuple[list[ElementModel], dict[str, list[ElementModel]]]:
        """Split each passage into basic elements."""
        all_elements: list[ElementModel] = []
        all_passages = self.all_passages or self.get_all_passages_info()[0]
        patterns = {Patterns.Comment, Patterns.Macro, Patterns.Tag}

        for passage in all_passages:
            all_elements = self._get_element_info(passage, patterns, all_elements)

        all_elements_by_passage: dict[str, list[ElementModel]] = defaultdict(list)
        for element in all_elements:
            all_elements_by_passage[element.passage].append(element)
        all_elements_by_passage = dict(all_elements_by_passage)

        self.all_closed_macros_names = self._get_all_closed_macros(all_elements)
        self.all_closed_tags_names = self._get_all_closed_tags(all_elements)
        all_elements, all_elements_by_passage = self._reclassify_elements(all_elements_by_passage, self.all_closed_macros_names, self.all_closed_tags_names)

        """ Temporarily saved. """
        with Session(ENGINE) as session:
            session.add_all(
                ElementModelTable(
                    filepath=element_model.filepath.relative_to(self.game_root).__str__(),
                    passage=element_model.passage,
                    widget=element_model.widget,
                    block=element_model.block,
                    block_name=element_model.block_name,
                    block_semantic_key=element_model.block_semantic_key,
                    type=element_model.type,
                    body=element_model.body,
                    pos_start=element_model.pos_start,
                    pos_end=element_model.pos_end,
                    length=element_model.length,
                    level=element_model.level,
                )
                for element_model in all_elements
            )
            session.commit()

        self.all_elements = all_elements
        self.all_elements_by_passage = all_elements_by_passage
        logger.success(f"{len(self.all_elements)} elements found.")

        """Debug texts, no actual use."""
        logger.debug(f"maximum length: {max(_.length for _ in all_elements)}")
        logger.debug(f"minimum length: {min(_.length for _ in all_elements)}")
        return all_elements, all_elements_by_passage

    def _get_element_info(self, passage: PassageModel, patterns: set[Patterns], all_elements: list[ElementModel]) -> list[ElementModel]:
        filepath = passage.filepath
        title = passage.title
        body = passage.body
        widget_flag = bool(passage.widgets)

        """special passage: [script]"""
        if passage.tag and passage.tag.lower() == "script":
            all_elements.append(ElementModel(
                filepath=filepath,
                passage=title,
                type=Patterns.JavaScript.name,
                body=body,
                pos_start=0,
                pos_end=len(body),
                length=len(body),
            ))
            return all_elements

        elements_found: list[ElementModel] = []
        """Elements have clear definition."""
        for pattern in patterns:
            for match in re.finditer(pattern.value, body):
                element = ElementModel(
                    filepath=filepath,
                    passage=title,
                    type=pattern.name,
                    body=match.group(),
                    pos_start=match.start(),
                    pos_end=match.end(),
                    length=match.end() - match.start(),
                )
                if widget_flag:
                    for widget in passage.widgets:
                        if match.start() >= widget.pos_start and match.end() <= widget.pos_end:
                            element.widget = widget.name
                            break
                elements_found.append(element)

        if not elements_found:
            elements_found.append(ElementModel(
                filepath=filepath,
                passage=title,
                type=Patterns.PlainText.name,
                body=body,
                pos_start=0,
                pos_end=len(body),
                length=len(body),
            ))

        elements_found = self._sort_elements(elements_found)
        elements_found = self._filter_elements_inside_another(elements_found)
        elements_found = self._fill_plaintexts(elements_found, filepath, body, passage, widget_flag)
        elements_found = self._merge_elements_inside_script(elements_found)
        all_elements.extend(elements_found)
        return all_elements

    """ Merge """  # TODO
    def merge_elements(self, length_limit: int = 10000, lines_limit: int = 50):
        """
        按照块和指定长度合并元素

        一段 Passage 的通用结构：

        前内容
        <头>
            前内容
            <块>
            块间内容
            <块>
            后内容
        </尾>
        块间内容
        <块>
        后内容

        处理步骤如下：
        1. 寻找第一个头
        1.1. 整个文章都没有头，则转入块间内容处理
        2. 寻找对应的尾
        3. 判断包括头尾在内的整个块长度是否超限
        3.1. 若未超限，则添加块
        3.2. 若超限，则头作为寻常块间内容处理，向下继续寻找新的头
        4. 块间内容处理（块间内容包括前内容和后内容）
        4.1. 判断整个块间内容长度是否超限
        4.1.1. 若未超限，将整个块间内容作为“块”添加
        4.1.2. 若超限，从前往后逐个添加元素直到最后一个未超限的元素，作为“块”添加，并重复直到块间内容无剩余
        """
        all_passages, all_passages_by_passage = (self.all_passages, self.all_passages_by_passage) if self.all_passages else self.get_all_passages_info()
        all_elements, all_elements_by_passage = (self.all_elements, self.all_elements_by_passage) if self.all_elements else self.get_all_elements_info()

        key_template = "{passage}{block}"

        """
        {语义化键: [块所包含的元素]}
        
        语义化键描述：
        - passage: 文章标题
        - block: 见下
        其中以上两者之间以两条竖线分隔(||)
        block 块之间以减号(-)分隔，块类型与块名称之间以两个冒号分割(::)，块序号以方括号包裹([])
        形如：
        - <块类型>::<块名称>[<块序号>]-<块类型>::<块名称>[<块序号>]
        如
        - Macro::if[2]-Tag::span[1]
        
        如一个完整的语义化键可以形如：
        - "Upgrade Waiting Room||Macro::if-Macro::silently[1]"
        - "Downgrade Waiting Room"
        
        block 的构建原理：
        对于所选块，按树状结构，依次包含从当前 passage 开头到所选块为止的，包裹着所选块的所有块的名称
        对同级块则记录在其同级中的顺序
        - 对于所选块，向上查询已经记录的块
        - 若块有尾，说明并非包裹所选块，
          - 若同名，说明为同级同名块，所选块序号+1
        - 无尾 若块有头 说明包裹所选块，记录其名称；同级序号写入，清零
        - 无尾 无头 说明遍历到的块位于文章开头 第一个块开头之前，忽略
        对于:
        < widget>
          < for>
            < if(0)>
              < link>
              </link>
            </if>
            < if(1)>
              < link>
              </link>
            </if>
          </for>
        </widget>
        其中if(1)块对应的语义化键简记为“widget-for-if(1)”
        1为同级序号，widget-for-if为按树状结构从文章开头到if(1)块为止包裹着if(1)的所有块的名称记录
        """
        result_blocks: dict[str, list[ElementModel]] = {}
        for passage_name, elements in all_elements_by_passage.items():
            # 1. passage 整段长度
            passage: PassageModel = all_passages_by_passage[passage_name]
            filepath_relative = passage.filepath.relative_to(self.game_root)
            if passage.length <= length_limit:
                key = key_template.format(filepath=filepath_relative, passage=f"||{passage_name}", block="")
                result_blocks[key] = elements
                continue

            # 2. 拆分成块，由外层向内层逐步判断
            current_block: list[ElementModel] = []
            is_in_block_macro: bool = False
            is_in_block_tag: bool = False

            # 进入外层循环，此循环中仅会出现 块开头 与 上一个块结束到下一个块开头之前的普通文本
            # 其他内容均在内层循环中处理
            for idx_head, element_head in enumerate(elements):
                # 因为一定会先出现开头，再出现结尾
                # 而结尾会在内部循环中处理
                # 故对于所有非开头均作为块间内容处理
                # 1.1. 非开头
                if element_head.block not in {ModelField.MacroBlockHead, ModelField.TagBlockHead}:
                    # TODO 块间内容处理
                    continue

                # 1.2. 开头
                # 仅当外层循环出现开头时，进入内层循环，向前窥视
                # 开头仅会出现一种，无须担心同时出现 macro 与 tag 均为 true 的情况
                if element_head.block == ModelField.MacroBlockHead.name:
                    current_block_name = element_head.block_name
                    is_in_block_macro = True
                else:   # Tag
                    current_block_name = element_head.block_name
                    is_in_block_tag = True

                # 开头加入块
                current_block.append(element_head)
                # 记录开头位置，当长度超限时使用。
                current_block_level = 0
                block_head_index = idx_head
                # 对于可能的头尾
                # 记录位置(0)，当长度超限时使用
                # 记录层数(1)，用于头尾配对用
                probable_block_heads: list[tuple[int, int, ElementModel]] = []
                probable_block_tails: list[tuple[int, int, ElementModel]] = []
                # 进入内层循环，即填充当前块
                for idx_peek, element_peek in enumerate(elements[idx_head:]):
                    if idx_peek == 0:  # element_peek = element
                        continue

                    # 因为一定会先出现当前块的结尾，再出现新块的开头，因此此处处理顺序为先处理头再处理尾
                    # 无需担心会因为找不到结尾而无法退出循环
                    # 1.1.1. 出现可能的开头时
                    if element_peek.block in {ModelField.MacroBlockHead, ModelField.TagBlockHead}:
                        # 先计算层数
                        current_block_level += 1
                        # 再记录位置
                        probable_block_heads.append((idx_head+idx_peek, current_block_level, element_peek))

                    # 1.1.2.出现可能的结尾时，
                    # 注意：
                    #   记录开头的顺序是由外层到内层，无需过多操作
                    #   记录结尾的顺序则不然，需要顺序遍历开头并寻找到首个未配对的、与自己同层数的开头，并占位
                    # 在占位后再修改层数(-=1)
                    if element_peek.block in {ModelField.MacroBlockTail, ModelField.TagBlockTail}:
                        # 先确定位置
                        # 此处原理：
                        #    头列表长度一定大于等于尾列表
                        #    且头按顺序加入头列表
                        #    且一个头一定对应一个尾，即仅会出现（头，尾）和（头1，头2，尾2，尾1）的情况，
                        #      不会出现（头1，尾2，头2，尾1）或（头1，头2，尾1，尾2）的情况
                        #    故当头列表长度增加时，新增加的头对应的尾一定在现有的尾之后
                        #    故在当前尾列表的末尾做延长即可
                        # 且不会多记录尾的数量，因此无需在退出当前块时做额外处理
                        probable_block_tails = [*probable_block_tails, *(None for _ in probable_block_heads[len(probable_block_tails):])]
                        for idx__, (pos, level, heads) in enumerate(probable_block_heads):
                            if level == current_block_level and probable_block_tails[idx__] is None:
                                probable_block_tails[idx__] = (idx_head+idx_peek, current_block_level, element_peek)
                                # 找到对应的就不用再遍历了
                                break
                        # 再计算层数
                        current_block_level -= 1

                        # 若层数为 -1 则说明当前块结束
                        # 先计算当前块长度，若未超限，则退出内部循环，直接计入结果中
                        if current_block_level == -1:
                            # 块长度包括开头和结尾的长度
                            current_block_length = sum(_.length for _ in current_block) + element_peek.length
                            if current_block_length <= length_limit:
                                # 结尾还没加入块中
                                current_block.append(element_peek)
                                # 语义化键构建
                                # 倒序搜索
                                current_block_key = ""
                                current_block_idx = 0

                                # for result_key, result_block in list(result_blocks.items()):
                                    # for result_element in result_block:
                                    #     # 只要出现头，就
                                    #     if result_element.block in {ModelField.MacroBlockTail.name, ModelField.TagBlockTail.name}

                                # for result_key, result_block in list(result_blocks.items())[::-1]:
                                #     # 若有尾，说明不包裹
                                #     if result_block[-1].block in {ModelField.MacroBlockTail.name, ModelField.TagBlockTail.name}:
                                #         _keys = result_key.split("||")
                                #         # 即上一块是整个 Passage，不过这种情况理论上不存在？FIXME
                                #         if len(_keys) != 2:
                                #             continue
                                #
                                #         result_block_type, result_block_name = _keys[-1].split("-")[-1].split("::")
                                #         result_block_name, result_block_idx = result_block_name.rstrip("]").split("[")
                                #
                                #         # 若同名，则当前块序号直接以上一块序号+1，否则为默认 0
                                #         if result_block_name == current_block_name:
                                #             current_block_idx = int(result_block_idx) + 1
                                #
                                #     # 若无尾有头，说明包裹
                                #     elif result_block[0].block in {ModelField.MacroBlockHead.name, ModelField.TagBlockHead.name}:
                                #         ...

                                key_block = f"||Macro::{current_block_name}" if is_in_block_macro else f"||Tag::{current_block_name}"
                                key = key_template.format(filepath=filepath_relative, passage=f"||{passage_name}", block=key_block)
                                result_blocks[key] = current_block
                                break

                        # 记录位置
                        probable_block_tails.insert(0, element_peek)

                    # 1.1.3. 既非开头又非结尾则不做处理，直接填充
                    # 填充块
                    current_block.append(element_peek)

    # def get_all_elements_info_detailed(self) -> list[ElementModel]:
    #     all_elements_by_passage = self.all_elements_by_passage or self.get_all_elements_info()[1]
    #     all_elements_by_passage_detailed = all_elements_by_passage.copy()
    #
    #     element_level = 0
    #     for passage, elements in all_elements_by_passage.items():
    #         for idx, element in enumerate(elements):
    #             match element.type:
    #                 case Patterns.Comment.name:
    #                     """ /* content */ """
    #                     content = re.match(Patterns.Comment.value, element.body).groups()[0]
    #                     element.data = ElementCommentModel(content=content)
    #                 case Patterns.Macro.name:
    #                     """ <<name args>> """
    #                     # TODO
    #                     name, args = re.match(Patterns.Macro.value, element.body).groups()
    #                     args_desugared = self.desugar(args) if args else None
    #                     element.body_desugared = f"<<{name} {args_desugared}>>" if args else element.body
    #                     if is_close := name.startswith("/"):
    #                         name = name.lstrip("/")
    #                     element.data = ElementMacroModel(name=name, args=args, is_close=is_close)
    #                 case Patterns.Tag.name:
    #                     """<name args>"""
    #                     # TODO
    #                     name, args = re.match(Patterns.Macro.value, element.body).groups()
    #                     if is_close := name.startswith("/"):
    #                         name = name.lstrip("/")
    #                     element.data = ElementTagModel(name=name, args=args, is_close=is_close)
    #                 case Patterns.PlainText.name:
    #                     # TODO
    #                     if element.body.startswith("$") or element.body.startswith("_"):
    #                         display_name = element.body
    #                         element.data = ElementVariableModel(display_name=display_name)
    #                     else:
    #                         element.data = ElementVariableModel()
    #                 case _:
    #                     raise TypeError(f"Unknown element type: {element.type}")
    #
    #             element.level = element_level
    #             all_elements_by_passage_detailed[passage][idx] = element
    #
    #     all_elements_detailed = []
    #     for passage, elements in all_elements_by_passage_detailed.items():
    #         all_elements_detailed.extend(elements)
    #
    #     with open(DIR_DATA / "all_elements_detailed.json", "w", encoding="utf-8") as fp:
    #         json.dump(
    #             [_.model_dump(mode="json") for _ in all_elements_detailed],
    #             fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
    #         )
    #
    #     with open(DIR_DATA / "all_elements_by_passage_detailed.json", "w", encoding="utf-8") as fp:
    #         json.dump(
    #             {k: [v.model_dump(mode="json") for v in vs] for k, vs in all_elements_by_passage_detailed.items()},
    #             fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
    #         )
    #
    # """ Restore TwineScript to JavaScript """
    # # TODO: Optimization
    # def restore_javascript(self):
    #     all_passages = self.all_passages or self.get_all_passages_info()[0]
    #     for idx, passage in enumerate(all_passages):
    #         logger.info(f"Restoring passage {idx}/{len(all_passages)}: {passage.title}")
    #         all_passages[idx].body = self.desugar(passage.body)
    #
    #     with open(DIR_DATA / "all_passages_desugared.json", "w", encoding="utf-8") as fp:
    #         json.dump(
    #             [_.model_dump(mode="json") for _ in all_passages],
    #             fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
    #         )
    #
    #     all_passages_by_passage = {
    #         passage_model.title: passage_model
    #         for passage_model in all_passages
    #     }
    #     with open(DIR_DATA / "all_passages_by_passage_desugared.json", "w", encoding="utf-8") as fp:
    #         json.dump(
    #             {k: v.model_dump(mode="json") for k, v in all_passages_by_passage.items()},
    #             fp, indent=2, ensure_ascii=False, escape_forward_slashes=False
    #         )
    #
    # def desugar(self, twinescript_code: str) -> str:
    #     """
    #     1. 变量: $ -> State.variables., ...
    #     2. 表达式: to -> ==, gte -> >=, ...
    #     """
    #     code = twinescript_code
    #     matches = list(re.finditer(Patterns.Desugar.value, code))
    #
    #     """替换字符串后顺序坐标会改变，因此倒序替换"""
    #     """no-op: Empty quotes, Double quoted, Single quoted, Operator characters, Spread/rest syntax"""
    #     for match in matches[::-1]:
    #         # Template literal, non-empty.
    #         if sugared_template := match[1]:
    #             template = self.desugar_template(sugared_template)
    #             if template != sugared_template:
    #                 code = (
    #                     f"{code[:match.start()]}"
    #                     f"{template}"
    #                     f"{code[match.start()+len(sugared_template):]}"
    #                 )
    #
    #         # Barewords.
    #         elif token := match[2]:
    #             # logger.info(f"match token: {idx}/{len(matches)} - {token}")
    #             """
    #             If the token is simply a dollar-sign or underscore, then it's either
    #             just the raw character or, probably, a function alias, so skip it.
    #             """
    #             if token in {'$', '_'}:
    #                 continue
    #
    #             """
    #             If the token is a story $variable or temporary _variable, then reset
    #             it to just its sigil for replacement.
    #             """
    #             if re.match(Patterns.Variable.value, token):
    #                 token = token[0]
    #
    #             """
    #             If the finalized token has a mapping, replace it within the code string
    #             with its counterpart.
    #             """
    #             if replacement := Mappings.Token.value.get(token):
    #                 code = (
    #                     f"{code[:match.start()]}"
    #                     f"{replacement}"
    #                     f"{code[match.start()+len(token):]}"
    #                 )
    #
    #     return code
    #
    # def desugar_template(self, twinescript_template: str) -> str:
    #     """ `...${content}...${...${nested_content}...}...` """
    #     template = twinescript_template
    #
    #     start_match_search_pos = 0
    #     while start_match := Patterns.TemplateGroupStart.value.search(template, pos=start_match_search_pos):
    #         depth = 1
    #
    #         start_index = start_match.start() + 2
    #         end_index = start_index
    #         end_match_search_pos = start_index
    #         while end_match := Patterns.TemplateGroupParse.value.search(template, pos=end_match_search_pos):
    #             # logger.info("loop 2")
    #             if end_match[1]:  # open
    #                 depth += 1
    #                 logger.info(f"{depth=}, {end_match=}")
    #             elif end_match[2]:  # close
    #                 depth -= 1
    #                 logger.info(f"{depth=}, {end_match=}")
    #
    #             if depth == 0:
    #                 end_index = end_match.start()
    #                 break
    #             end_match_search_pos = end_match.start() + 1
    #
    #         start_match_search_pos = start_index
    #         if end_index > start_index:
    #             old = template[start_index:end_index]
    #             new = self.desugar(old)
    #
    #             template = (
    #                 f"{template[:start_index]}"
    #                 f"{new}"
    #                 f"{template[start_index+len(old):]}"
    #             )
    #             start_match_search_pos += len(new) - len(old)
    #             continue
    #
    #     return template

    """ Utility Methods """
    @staticmethod
    def _split_widgets(passage_name: str, passage_body: str) -> list[WidgetModel]:
        """Split each widget in single widget-passage into parts."""
        widget_pattern = re.compile(rf"""{Patterns.MacroWidget.value.pattern}([\s\S]*?)<</widget>>""")
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
                length=len(widget_body),
                passage=passage_name
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
    def _fill_plaintexts(elements: list[ElementModel], filepath: Path, content: str, passage: PassageModel, widget_flag: bool) -> list[ElementModel]:
        """经过处理后，夹在两个元素之间的就是纯文本"""
        elements_copy = elements.copy()
        for idx, element in enumerate(elements_copy):
            """向前判断一次"""
            # 在开头之前可能有纯文本
            if idx == 0 and element.pos_start > 0:
                text = content[:element.pos_start]
                pos_start = 0
                pos_end = element.pos_start
                element_ = ElementModel(
                    filepath=filepath,
                    passage=passage.title,
                    type=Patterns.PlainText.name,
                    body=text,
                    pos_start=pos_start,
                    pos_end=pos_end,
                    length=pos_end - pos_start,
                )
                if widget_flag:
                    for widget in passage.widgets:
                        if pos_start >= widget.pos_start and pos_end <= widget.pos_end:
                            element_.widget = widget.name
                            break
                elements.insert(0, element_)

            """向后判断一次"""
            # 非开头 非末尾
            if idx < len(elements_copy) - 1:
                # 前后两元素中间没有内容
                if element.pos_end == elements_copy[idx+1].pos_start:
                    continue

                text = content[element.pos_end:elements_copy[idx+1].pos_start]
                pos_end = elements_copy[idx+1].pos_start

            # 在末尾之后可能有纯文本
            else:
                # 元素末尾就是段落末尾
                if element.pos_end >= len(content):
                    continue

                text = content[element.pos_end:]
                pos_end = len(content)

            pos_start = element.pos_end
            element_ = ElementModel(
                filepath=filepath,
                passage=passage.title,
                type=Patterns.PlainText.name,
                body=text,
                pos_start=pos_start,
                pos_end=pos_end,
                length=pos_end - pos_start,
            )
            if widget_flag:
                for widget in passage.widgets:
                    if pos_start >= widget.pos_start and pos_end <= widget.pos_end:
                        element_.widget = widget.name
                        break
            elements.insert(idx+1, element_)
        """Sort again, including plain-text elements"""
        return Twee3Parser._sort_elements(elements)

    @staticmethod
    def _merge_elements_inside_script(elements: list[ElementModel], block_start: str = "<<script>>", block_end: str = "<</script>>") -> list[ElementModel]:
        """
        <<script>>...<</script>>
        之中的内容统一判断为 JAVASCRIPT

        <script>...</script>
        也是
        """
        result: list[ElementModel] = []
        filepath = elements[0].filepath
        passage = elements[0].passage
        type_ = Patterns.JavaScript.name
        pos_start = -1
        body = ""

        inside = False
        for element in elements:
            if not inside:  # <<script>> / <script> ，及其它元素
                result.append(element)
            elif element.body == block_end:
                inside = False
                result.extend((
                    ElementModel(
                        filepath=filepath,
                        passage=passage,
                        type=type_,
                        pos_start=pos_start,
                        pos_end=element.pos_start,
                        length=element.pos_start-pos_start,
                        body=body,
                        widget=element.widget
                    ),
                    element
                ))
                continue
            else:  # 二者之间的元素，以及 <</script>> / </script>
                body = f"{body}{element.body}"
                continue

            if element.body == block_start:
                inside = True
                pos_start = element.pos_end
                body = ""
        return result

    @staticmethod
    def _merge_elements_inside_script_macro(elements: list[ElementModel]) -> list[ElementModel]:
        """<<script>>...<</script>>"""
        return Twee3Parser._merge_elements_inside_script(elements)

    @staticmethod
    def _merge_elements_inside_script_tag(elements: list[ElementModel]) -> list[ElementModel]:
        """<script>...</script>"""
        return Twee3Parser._merge_elements_inside_script(elements, block_start="<script>", block_end="</script>")

    @staticmethod
    def _get_all_closed_macros(all_elements: list[ElementModel]) -> set[str]:
        """获取所有在文中出现过的需闭合的 macro | by HCP"""
        all_macros: list[ElementModel] = list(filter(lambda element: element.type == Patterns.Macro.name, all_elements))

        """正常定义的闭合标签 <</macro>>"""
        return {macro.body.lstrip("<</").rstrip(">>") for macro in all_macros if macro.body.startswith("<</")}

        # FIXME 暂不考虑
        # """非正常定义的闭合标签 <<endmacro>>"""
        # probably_closed_macros: list[ElementModel] = list(filter(lambda element: element.body.startswith("<<end"), all_macros))
        # probably_closed_macros_names: set[str] = set(filter(lambda name: name.startswith("end"), all_macros_names))
        # logger.info(f"全文疑似共有{len(probably_closed_macros_names)}种定义的 macro 非常规闭合标签")
        #
        # # 根据定义排除非闭合标签，如 <<endevent>>
        # all_widget_macros: list[ElementModel] = list(filter(lambda element: element.body.startswith("<<widget"), all_macros))
        # all_widget_macros_names: set[str] = {re.match(Patterns.Macro.value, element.body).groups()[1].rstrip("container").strip().strip('"') for element in all_widget_macros}
        # all_widget_macros_names_startswith_end: set[str] = set(filter(lambda name: name.startswith("end"), all_widget_macros_names))
        # logger.info(f"全文共有{len(all_widget_macros_names_startswith_end)}种定义的 end 开头的 macro")
        #
        # probably_closed_macros_names = probably_closed_macros_names - all_widget_macros_names_startswith_end
        # logger.info(f"全文疑似共有{len(probably_closed_macros_names)}种定义的 macro 非常规闭合标签")
        # logger.info("|".join(probably_closed_macros_names))

    @staticmethod
    def _get_all_closed_tags(all_elements: list[ElementModel]) -> set[str]:
        """获取所有在文中出现过的需闭合的 tags"""
        all_tags: list[ElementModel] = list(filter(lambda element: element.type == Patterns.Tag.name, all_elements))

        """正常定义的闭合标签 </div>"""
        return {macro.body.lstrip("</").rstrip(">") for macro in all_tags if macro.body.startswith("</")}

    @staticmethod
    def _reclassify_elements(all_elements_by_passage: dict[str, list[ElementModel]], all_closed_macros_names: set[str], all_closed_tags_names: set[str]) -> tuple[list[ElementModel], dict[str, list[ElementModel]]]:
        """将元素按照“块”、“内容”重分类为两类，并构建语义化键"""
        """
        {PassageName}
        ||
        {BlockType}::{BlockName}[{BlockIndex}]
        -
        {BlockType}::{BlockName}[{BlockIndex}]
        ...
        """
        _keys = defaultdict(list)
        global_level: int = 0
        for passage_name, elements in all_elements_by_passage.items():
            for idx, element in enumerate(elements):
                match element.type:
                    case Patterns.Macro.name:
                        macro_name = Patterns.Macro.value.match(element.body).groups()[0]
                        macro_name_open = macro_name.lstrip("/")
                        if macro_name_open in all_closed_macros_names:
                            if macro_name == macro_name_open:
                                all_elements_by_passage[passage_name][idx].block = ModelField.MacroBlockHead.name
                                global_level += 1
                            else:
                                all_elements_by_passage[passage_name][idx].block = ModelField.MacroBlockTail.name
                                all_elements_by_passage[passage_name][idx].level = global_level  # 先记录层数再减
                                global_level -= 1
                            all_elements_by_passage[passage_name][idx].block_name = macro_name_open

                    case Patterns.Tag.name:
                        tag_name, is_tag_self_close = Patterns.Tag.value.match(element.body).groups()
                        tag_name_open = tag_name.lstrip("/")

                        # 有些特殊 tag 既能自闭也能不自闭，如 <image>
                        is_tag_self_close = bool(is_tag_self_close)
                        if tag_name_open in all_closed_tags_names:
                            if tag_name == tag_name_open:
                                if not is_tag_self_close:
                                    all_elements_by_passage[passage_name][idx].block = ModelField.TagBlockHead.name
                                    global_level += 1
                            else:
                                all_elements_by_passage[passage_name][idx].block = ModelField.TagBlockTail.name
                                all_elements_by_passage[passage_name][idx].level = global_level  # 先记录层数再减
                                global_level -= 1
                            all_elements_by_passage[passage_name][idx].block_name = tag_name_open
                # 层数
                all_elements_by_passage[passage_name][idx].level = global_level if all_elements_by_passage[passage_name][idx].level == -1 else all_elements_by_passage[passage_name][idx].level

                # 构建语义化键：
                # 仅对块首元素构建：
                _current_element: ElementModel = all_elements_by_passage[passage_name][idx]
                if _current_element.block in {ModelField.MacroBlockHead.name, ModelField.TagBlockHead.name}:
                    _semantic_key: str = ""
                    _semantic_key_idx: int = 0
                    _have_met_same_level: bool = False
                    # 从当前元素开始倒序向前找，
                    for _result_element in all_elements_by_passage[passage_name][:idx][::-1]:
                        # 仅找块首元素
                        if _result_element.block not in {ModelField.MacroBlockHead.name, ModelField.TagBlockHead.name}:
                            continue

                        # 遇到层数大的则跳过 (其他块的内部，无关自己的键)，
                        if _result_element.level > _current_element.level:
                            continue
                        # 遇到首个层数小的，则将自己的键添加在对方之后，并跳出 (跳出包裹了)
                        elif _result_element.level < _current_element.level:
                            _semantic_key = f"{_result_element.block_semantic_key}-"
                            break

                        # 遇到首个同一层数的，判断名称类型
                        # 遇到首个同一层数且同名同类，则自己的序号为对方的序号+1，此后不再判断同一层数直到跳出
                        # 若始终没遇到首个同一层数，说明该元素块序号是 [0]，无需额外处理
                        if _have_met_same_level:
                            continue

                        if _result_element.block_name == _current_element.block_name and _result_element.type == _current_element.type:
                            _have_met_same_level = True
                            _semantic_key_idx = int(_result_element.block_semantic_key.rstrip("]").split("[")[-1]) + 1

                    # 直到遍历完都没有跳出，即该元素为首个块首元素
                    # 添加文章名称头部
                    else:
                        _semantic_key = f"{element.passage}||"

                    # 完整的语义化键
                    # eg: Upgrade Waiting Room||Macro::if[0]-Macro::silently[1]
                    all_elements_by_passage[passage_name][idx].block_semantic_key = f"{_semantic_key}{_current_element.type}::{_current_element.block_name}[{_semantic_key_idx}]"
                    # logger.info(f"[{passage_name}] {all_elements_by_passage[passage_name][idx].block_semantic_key}")

        all_elements = []
        for elements in all_elements_by_passage.values():
            all_elements.extend(elements)
        return all_elements, all_elements_by_passage

    @staticmethod
    def _build_semantic_keys():
        """TODO 为每个“头”、“尾”元素构建语义化键"""

    """ Getters & Setters """

    @property
    def suffix(self) -> str:
        return self._suffix

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
    def all_elements(self) -> list[ElementModel]:
        return self._all_elements

    @all_elements.setter
    def all_elements(self, elements: list[ElementModel]) -> None:
        self._all_elements = elements

    @property
    def all_elements_by_passage(self) -> dict[str, list[ElementModel]]:
        return self._all_elements_by_passage

    @all_elements_by_passage.setter
    def all_elements_by_passage(self, elements_by_passage: dict[str, list[ElementModel]]) -> None:
        self._all_elements_by_passage = elements_by_passage

    @property
    def all_closed_macros_names(self) -> set[str]:
        return self._all_closed_macros_names

    @all_closed_macros_names.setter
    def all_closed_macros_names(self, macros_names: set[str]) -> None:
        self._all_closed_macros_names = macros_names

    @property
    def all_closed_tags_names(self) -> set[str]:
        return self._all_closed_tags_names

    @all_closed_tags_names.setter
    def all_closed_tags_names(self, tags_names: set[str]) -> None:
        self._all_closed_tags_names = tags_names


# class MacroArgumentParser:
#     def __init__(self):
#         self._space_regex: re.Pattern = Patterns.Space.value
#         self._not_space_regex: re.Pattern = Patterns.NotSpace.value
#         self._var_test_regex: re.Pattern = re.compile(f"^{Patterns.Variable.value}")
#
#     """ Lex methods """
#     @staticmethod
#     def slurp_quote(lexer: Lexer, end_quote: str) -> int:
#         while True:
#             ch = lexer.next()
#             if ch == "\\":
#                 next_ch = lexer.next()
#                 if next_ch not in (Lexer.EOF, "\n"):
#                     continue
#
#             elif ch in {Lexer.EOF, '\n'}:
#                 return Lexer.EOF
#
#             elif ch == end_quote:
#                 break
#
#         return lexer.pos
#
#     def lex_space(self, lexer: Lexer) -> Callable[[Lexer], ...] | None:
#         offset = self.not_space_regex.search(lexer.source[lexer.pos:])
#         if offset is None:
#             return None
#         elif offset.start():
#             lexer.pos += offset.start()
#             lexer.ignore()
#
#         match lexer.next():
#             case '`': return self.lex_expression
#             case '"': return self.lex_double_quote
#             case "'": return self.lex_single_quote
#             case '[': return self.lex_square_bracket
#             case _: return self.lex_bare_word
#
#     def lex_expression(self, lexer: Lexer) -> Callable[[Lexer], ...] | None:
#         if self.slurp_quote(lexer, '`') == Lexer.EOF:
#             return Lexer.error(MacroArgumentParserItem.Error, 'unterminated backquote(`) expression')
#
#         lexer.emit(MacroArgumentParserItem.Expression)
#         return self.lex_space
#
#     def lex_double_quote(self, lexer: Lexer) -> Callable[[str], ...] | None:
#         if self.slurp_quote(lexer, '"') == Lexer.EOF:
#             return Lexer.error(MacroArgumentParserItem.Error, 'unterminated double quoted(") expression')
#
#         lexer.emit(MacroArgumentParserItem.String)
#         return self.lex_space
#
#     def lex_single_quote(self, lexer: Lexer) -> Callable[[str], ...] | None:
#         if self.slurp_quote(lexer, "'") == Lexer.EOF:
#             return Lexer.error(MacroArgumentParserItem.Error, 'unterminated single quoted string(\') expression')
#
#         lexer.emit(MacroArgumentParserItem.String)
#         return self.lex_space
#
#     def lex_square_bracket(self, lexer: Lexer) -> Callable[[str], ...] | None:
#         img_meta = '<>IiMmGg'
#
#         if lexer.accept(img_meta):
#             what = 'image'
#             lexer.accept_run(img_meta)
#         else:
#             what = 'link'
#
#         if not lexer.accept('['):
#             return lexer.error(MacroArgumentParserItem.Error, f'malformed {what} markup')
#
#         # account for both initial left square brackets
#         lexer.depth = 2
#         while True:
#             ch = lexer.next()
#             if ch == "\\":
#                 next_ch = lexer.next()
#                 if next_ch not in (Lexer.EOF, "\n"):
#                     continue
#
#             elif ch in {Lexer.EOF, '\n'}:
#                 return lexer.error(MacroArgumentParserItem.Error, f'unterminated {what} markup')
#
#             elif ch == "[":
#                 lexer.depth += 1
#                 continue
#
#             elif ch == "]":
#                 lexer.depth -= 1
#                 if lexer.depth < 0:
#                     return lexer.error(MacroArgumentParserItem.Error, 'unexpected right square bracket "]"')
#
#                 elif lexer.depth == 1:
#                     if lexer.next() == "]":
#                         lexer.depth -= 1
#                         break
#                     lexer.backup()
#
#                 continue
#
#         lexer.emit(MacroArgumentParserItem.SquareBracket)
#         return self.lex_space
#
#     def lex_bareword(self, lexer: Lexer) -> Callable[[str], ...] | None:
#         offset = self.space_regex.search(lexer.source[lexer.pos:])
#         lexer.pos = len(lexer.source) if offset is None else lexer.pos + offset.start()
#         lexer.emit(MacroArgumentParserItem.Bareword)
#         return None if offset is None else self.lex_space
#
#     """ Parse methods """
#     def parse_macro_arguments(self, raw_argument: str) -> list[LexerItemModel]:
#         lexer = Lexer(raw_argument, self.lex_space)
#         args = []
#
#         for item in lexer.run():
#             arg = item.text
#
#             match item.type_:
#                 case MacroArgumentParserItem.Error:
#                     raise Exception(f'unable to parse macro argument "{arg}": {item.message}')
#
#                 case MacroArgumentParserItem.Bareword:
#                     # A variable, so substitute its value.
#                     if self.var_test_regex.match(arg):
#                         arg = eval_twinescript(arg)  # TODO: evalTwineScript 的实现/变量作用域
#
#                     # Property access on the settings or setup objects, so try to evaluate it.
#                     elif re.compile(r'^(?:settings|setup)[.[]').match(arg):
#                         try:
#                             arg = eval_twinescript(arg)
#                         except Exception as e:
#                             raise Exception(f'unable to parse macro argument "${arg}": ${e}')
#
#                     # Null literal, so convert it into null.
#                     elif arg == 'null':
#                         arg = None
#
#                     # Undefined literal, so convert it into undefined.
#                     elif arg == 'undefined':
#                         arg = "undefined"
#
#                     # Boolean true literal, so convert it into true.
#                     elif arg == 'true':
#                         arg = True
#
#                     #
#
#                 case MacroArgumentParserItem.Expression:
#                     # remove the backquotes and trim the expression
#                     arg = arg[1:-1].strip()
#
#                     # Empty backquotes.
#                     if not arg:
#                         arg = "undefined"  # TODO: 改进
#
#                     # Evaluate the expression.
#                     else:
#                         try:
#                             """
#                             The enclosing parenthesis here are necessary to force a code string
#                             consisting solely of an object literal to be evaluated as such, rather
#                             than as a code block.
#                             """
#                             arg = eval_twinescript(f"({arg})")
#                         except Exception as e:
#                             raise Exception(f'unable to parse macro argument expression "${arg}": ${e}')
#
#                     break
#
#                 case MacroArgumentParserItem.String:
#                     # Evaluate the string to handle escaped characters.
#                     try:
#                         arg = eval_javascript(js_code=arg)
#                     except Exception as e:
#                         raise Exception(f'unable to parse macro argument string "{arg}": {e}')
#                     break
#
#                 case MacroArgumentParserItem.SquareBracket:
#                     ...
#
#             args.append(arg)
#
#         return args
#
#     """ Getters & Setters """
#     @property
#     def space_regex(self) -> re.Pattern:
#         return self._space_regex
#
#     @property
#     def not_space_regex(self) -> re.Pattern:
#         return self._not_space_regex
#
#     @property
#     def var_test_regex(self) -> re.Pattern:
#         return self._var_test_regex


__all__ = [
    "Twee3Parser"
]


if __name__ == '__main__':
    parser = Twee3Parser()
    # parser.get_all_passages_info()
    parser.get_all_elements_info()
