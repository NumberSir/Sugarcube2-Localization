from collections import defaultdict

from pathlib import Path
from sqlalchemy import distinct
from sqlalchemy.orm import Session
from typing import Iterator

from sugarcube2_localization.database import ENGINE
from sugarcube2_localization.log import logger
from sugarcube2_localization.exceptions import GameRootNotExistException

from sugarcube2_localization.core.reviewer.internal import Reviewer
from sugarcube2_localization.core.utils import get_all_filepaths
from sugarcube2_localization.core.schema.enum import ModelField
from sugarcube2_localization.core.schema.data_model import PassageModel, ElementModel
from sugarcube2_localization.core.schema.sql_model import PassageModelTable, ElementModelTable


class Twee3Reviewer(Reviewer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_all_filepaths(self) -> Iterator[Path]:
        """Get all javascript absolute filepaths."""
        if not self.game_root.exists():
            raise GameRootNotExistException
        return get_all_filepaths(".js", self.game_root / "game")

    def validate_all_elements(self):
        """检查提取出来的元素是否有遗漏、重复"""
        with Session(ENGINE) as session:
            _all_passages = session.query(PassageModelTable).all()
            all_passages_by_passage_models: dict[str, PassageModel] = {
                _passage.title: PassageModel.model_validate(_passage, from_attributes=True)
                for _passage in _all_passages
            }

            _all_elements = session.query(ElementModelTable).all()
            _all_passages_names = session.query(distinct(ElementModelTable.passage)).all()
            all_elements_by_passage_models: dict[str, list[ElementModel]] = defaultdict(list)
            for _element in _all_elements:
                all_elements_by_passage_models[_element.passage].append(
                    ElementModel.model_validate(_element, from_attributes=True)
                )

        """检查提取元素是否有遗漏"""
        validation_order = self._validate_all_elements_order(all_passages_by_passage_models, all_elements_by_passage_models)

        """检查元素拼接后是否等于原文章"""
        validation_reversible = self._validate_all_elements_reversible(all_passages_by_passage_models, all_elements_by_passage_models)

        """检查文章的元素层级是否正常"""
        validation_level = self._validate_all_elements_level_in_passage(all_elements_by_passage_models)

    @staticmethod
    def _validate_all_elements_order(all_passages_by_passage_models: dict[str, PassageModel], all_elements_by_passage_models: dict[str, list[ElementModel]]) -> dict[str, bool]:
        """顺序，有无遗漏"""
        result = {}
        for passage, elements in all_elements_by_passage_models.items():
            if elements[0].pos_start != 0 or elements[-1].pos_end != all_passages_by_passage_models[passage].length:
                result[passage] = False
                logger.warning(f"'{passage}'提取元素恐有遗漏 - {f'首元素开头并非文章开头: {elements[0].pos_start}' if elements[0].pos_start != 0 else f'末元素结尾未达文章结尾: {elements[-1].pos_end}'}")
                continue

            for idx, element in enumerate(elements):
                if idx == len(elements) - 1:
                    continue

                if element.pos_end != elements[idx+1].pos_start:
                    result[passage] = False
                    logger.warning(f"'{passage}'提取元素恐有遗漏 - 前后元素有间隙: {element.pos_end} ~ {elements[idx+1].pos_start}")
                    break

            else:
                result[passage] = True
                logger.debug(f"'{passage}'提取元素无遗漏")

        return result

    @staticmethod
    def _validate_all_elements_reversible(all_passages_by_passage_models: dict[str, PassageModel], all_elements_by_passage_models: dict[str, list[ElementModel]]) -> dict[str, bool]:
        """可逆，即元素可以拼回去"""
        result = {}
        for passage, elements in all_elements_by_passage_models.items():
            merged = "".join(element.body for element in elements)

            if merged != all_passages_by_passage_models[passage].body:
                logger.warning(f"'{passage}'拼接后与原文不同")
                result[passage] = False
                continue

            logger.debug(f"'{passage}'可以复原")
            result[passage] = True

        return result

    @staticmethod
    def _validate_all_elements_level_in_passage(all_elements_by_passage_models: dict[str, list[ElementModel]]) -> dict[str, bool]:
        """正常文章首尾元素层级为0，除非首尾元素为块头尾，此时层级为1"""
        result = {}
        for passage, elements in all_elements_by_passage_models.items():
            _is_head_element_blockhead = elements[0].block in {ModelField.MacroBlockHead.name, ModelField.TagBlockHead.name}
            _is_head_element_blockhead_and_level_normal = elements[0].level == 1 and _is_head_element_blockhead
            _is_head_element_plaintext_and_level_normal = elements[0].level == 0 and not _is_head_element_blockhead
            if not _is_head_element_blockhead_and_level_normal and not _is_head_element_plaintext_and_level_normal:
                logger.warning(f"'{passage}'首元素层级有误 - level='{elements[0].level}', body='{elements[0].body}'")

            _is_tail_element_blocktail = elements[-1].block in {ModelField.MacroBlockTail.name, ModelField.TagBlockTail.name}
            _is_tail_element_blocktail_and_level_normal = elements[-1].level == 1 and _is_tail_element_blocktail
            _is_tail_element_plaintext_and_level_normal = elements[-1].level == 0 and not _is_tail_element_blocktail
            if not _is_tail_element_blocktail_and_level_normal and not _is_tail_element_plaintext_and_level_normal:
                logger.warning(f"'{passage}'尾元素层级有误 - level='{elements[-1].level}', body='{elements[-1].body}'")

        return result


__all__ = [
    "Twee3Reviewer"
]


if __name__ == '__main__':
    reviewer = Twee3Reviewer()
    reviewer.validate_all_elements()

