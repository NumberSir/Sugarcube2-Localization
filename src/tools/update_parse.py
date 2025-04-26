"""一次性文件，将旧汉化转为新汉化"""
import time

import ujson as json

from src.config import settings
from src.log import logger
from src.toast import Toaster


class UpdateParse:
    def __init__(self):
        self._i18n: dict | None = None
        self._i18n_by_passage: dict | None = None
        self._all_elements: dict | None = None
        self._all_elements_by_passage: dict | None = None
        self._all_passages: list | None = None
        self._all_passages_by_passage: dict | None = None
        self._mappings: list | None = None
        self._mappings_by_passage: dict | None = None

    def read_data(self):
        with open("i18n.json", "r", encoding="utf-8") as fp:
            i18n = json.load(fp)
        self._i18n = i18n

        with open(settings.file.root / settings.file.data / "all_passages.json", "r", encoding="utf-8") as fp:
            all_passages = json.load(fp)
        self._all_passages = all_passages

    def get_mappings_before_update(self):
        """获取每一条汉化被那些基础元素前后包裹的信息"""
        all_passages_by_passage = {}
        for passage in self._all_passages:
            if passage["passage_title"] not in all_passages_by_passage:
                all_passages_by_passage[passage["passage_title"]] = passage
            else:
                continue

        with open("all_passages_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(all_passages_by_passage, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)
        self._all_passages_by_passage = all_passages_by_passage

        javascript: list[dict] = self._i18n["typeB"]["TypeBOutputText"]
        twine: list[dict] = self._i18n["typeB"]["TypeBInputStoryScript"]

        i18n_by_passage = {}
        for data in twine:
            if data["pN"] not in i18n_by_passage:
                i18n_by_passage[data["pN"]] = [data]
            else:
                i18n_by_passage[data["pN"]].append(data)

        with open("i18n_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(i18n_by_passage, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)
        self._i18n_by_passage = i18n_by_passage

        with open(settings.file.root / settings.file.data / "all_elements.json", "r", encoding="utf-8") as fp:
            all_elements = json.load(fp)
        self._all_elements = all_elements

        all_elements_by_passage = {}
        for idx, element in enumerate(all_elements):
            if element["passage_title"] not in all_elements_by_passage:
                all_elements_by_passage[element["passage_title"]] = [element]
            else:
                all_elements_by_passage[element["passage_title"]].append(element)

        with open("all_elements_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(all_elements_by_passage, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)
        self._all_elements_by_passage = all_elements_by_passage

        result = {}
        for passage_title, lines in i18n_by_passage.items():
            for idx_line, line in enumerate(lines):
                line_start = line["pos"]
                line_end = line_start + len(line['f'])

                pair = {
                    "passage_title": passage_title,
                    "idx_line": idx_line,
                    "line_en": line["f"],
                    "line_zh": line["t"]
                }
                for idx_element, element in enumerate(all_elements_by_passage[passage_title]):
                    element_start = element["pos_start"]
                    element_end = element["pos_end"]
                    # 元素 A (上确界)
                    if element_start <= line_start <= element_end:
                        pair["idx_element_start"] = idx_element

                    # 元素 B (下确界)
                    if element_start <= line_end <= element_end:
                        pair["idx_element_end"] = idx_element
                        break

                if passage_title not in result:
                    result[passage_title] = [pair]
                else:
                    result[passage_title].append(pair)

        with open("mappings_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2, escape_forward_slashes=False)

        self._mappings_by_passage = result
        return result

    def merge(self):
        """确定汉化行/原文元素的合并方式"""
        for passage_title, mappings in self._mappings_by_passage.items():

            merged_mapping = []
            for idx, mapping in enumerate(mappings):
                idx_line = mapping["idx_line"]
                if idx_line in merged_mapping:  # 已经合并了
                    continue

                merged_mapping.append(idx_line)
                if idx == len(mappings) - 1:  # 末尾，不用向后比较了
                    break

                idx_element_start = mapping["idx_element_start"]
                idx_element_end = mapping["idx_element_end"]
                for idx_compared, mapping_compared in enumerate(mappings[idx+1:]):
                    if all({
                        idx_element_start != mapping_compared["idx_element_start"],
                        idx_element_end != mapping_compared["idx_element_end"]
                    }):  # 这两个汉化行已经没有交集了
                        break
                    merged_mapping.append(mapping_compared["idx_line"])


if __name__ == '__main__':
    start = time.time()
    update = UpdateParse()
    update.read_data()
    update.get_mappings_before_update()
    update.merge()
    end = time.time()
    logger.info(f"{end - start}s")
    Toaster(
        title="汉化映射",
        body=[
            "映射完毕啦！",
            f"耗时 {end-start}s"
        ]
    ).notify()