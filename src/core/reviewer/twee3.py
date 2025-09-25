import json


from pathlib import Path
from typing import Iterator

from src.log import logger
from src.config import DIR_DATA
from src.exceptions import GameRootNotExistException
from src.core.reviewer.internal import Reviewer
from src.core.utils import get_all_filepaths
from src.core.schema.model import PassageModel, ElementModel


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
        with (DIR_DATA / "all_passages_by_passage.json").open("r", encoding="utf-8") as fp:
            all_passages_by_passage = json.load(fp)
        all_passages_by_passage_models: dict[str, PassageModel] = {
            passage: PassageModel.model_validate(content)
            for passage, content in all_passages_by_passage.items()
        }

        with (DIR_DATA / "all_elements_by_passage.json").open("r", encoding="utf-8") as fp:
            all_elements_by_passage = json.load(fp)
        all_elements_by_passage_models: dict[str, list[ElementModel]] = {
            passage: [
                ElementModel.model_validate(_)
                for _ in elements
            ]
            for passage, elements in all_elements_by_passage.items()
        }

        """检查提取元素是否有遗漏"""
        # validation_order = self._validate_all_elements_order(all_passages_by_passage_models, all_elements_by_passage_models)

        """检查元素拼接后是否等于原文章"""
        validation_reversible = self._validate_all_elements_reversible(all_passages_by_passage_models, all_elements_by_passage_models)

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
                logger.success(f"'{passage}'提取元素无遗漏")

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

            logger.success(f"'{passage}'可以复原")
            result[passage] = True

        return result


__all__ = [
    "Twee3Reviewer"
]


if __name__ == '__main__':
    reviewer = Twee3Reviewer()
    reviewer.validate_all_elements()

