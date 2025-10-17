"""一次性文件，将旧汉化转为新汉化"""
import time

import ujson as json

from sugarcube2_localization.config import DIR_DATA
from sugarcube2_localization.log import logger
from sugarcube2_localization.toast import Toaster


class UpdateParse:
    """TODO"""
    def __init__(self):
        self._i18n: dict | None = None
        self._i18n_by_passage: dict | None = None
        self._all_elements: dict | None = None
        self._all_elements_by_passage: dict | None = None
        self._all_passages: list | None = None
        self._all_passages_by_passage: dict | None = None
        self._mappings: list | None = None
        self._mappings_by_passage: dict | None = None
        self._merged_mappings: list | None = None
        self._merged_mappings_by_passage: dict | None = None
        self._converted_i18n: dict | None = None
        self._converted_i18n_by_passage: dict | None = None

    def read_data(self):
        with open("i18n.json", "r", encoding="utf-8") as fp:
            i18n = json.load(fp)
        self._i18n = i18n

        with open(DIR_DATA / "all_passages.json", "r", encoding="utf-8") as fp:
            all_passages = json.load(fp)
        self._all_passages = all_passages

    def get_mappings_before_update(self):
        """获取每一条汉化被哪些基础元素前后包裹的信息"""
        with open(DIR_DATA / "all_passages_by_passage.json", "r", encoding="utf-8") as fp:
            all_passages_by_passage = json.load(fp)
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

        with open(DIR_DATA / "all_elements.json", "r", encoding="utf-8") as fp:
            all_elements = json.load(fp)
        self._all_elements = all_elements

        with open(DIR_DATA / "all_elements_by_passage.json", "r", encoding="utf-8") as fp:
            all_elements_by_passage = json.load(fp)
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
        """
        对两个相邻汉化行：
        开头元素=开头元素 或 末尾元素=末尾元素
        则合并
        否则不合并
        
        如：
        [0, 0], [0, 0], [0, 1] => 合并
        [0, 1], [1, 1], [1, 2] => 合并
        [0, 1] | [2, 3] | [4, 5] => 不合并
        """
        pre_merged_mappings_by_passage = {}
        for passage_title, mappings in self._mappings_by_passage.items():
            pre_merged_mappings_by_passage[passage_title] = []
            is_merged = set()
            for idx, mapping in enumerate(mappings):
                idx_line = mapping["idx_line"]
                if idx_line in is_merged:  # 已经合并了
                    continue

                is_merged.add(idx_line)
                merged_mappings = [mapping]
                if idx == len(mappings) - 1:  # 末尾，不用向后比较了
                    pre_merged_mappings_by_passage[passage_title].append(merged_mappings)
                    break

                idx_element_start = mapping["idx_element_start"]
                idx_element_end = mapping["idx_element_end"]
                for idx_compared, mapping_compared in enumerate(mappings[idx+1:]):
                    if all({
                        idx_element_start != mapping_compared["idx_element_start"],
                        idx_element_end != mapping_compared["idx_element_end"]
                    }):  # 这两个汉化行已经没有交集了
                        break
                    merged_mappings.append(mapping_compared)
                    is_merged.add(mapping_compared["idx_line"])
                pre_merged_mappings_by_passage[passage_title].append(merged_mappings)

        with open("pre_merged_mappings_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(pre_merged_mappings_by_passage, fp, ensure_ascii=False, indent=2)

        merged_mappings_by_passage = {}
        for passage_title, pre_merged_mappings in pre_merged_mappings_by_passage.items():
            merged_mappings_by_passage[passage_title] = []
            for pre_merged_mapping in pre_merged_mappings:
                if len(pre_merged_mapping) == 1:
                    merged_mappings_by_passage[passage_title].append({
                        "pos": self._i18n_by_passage[passage_title][pre_merged_mapping[0]["idx_line"]]["pos"],
                        **{k: v for k, v in pre_merged_mapping[0].items() if k != "idx_line"}
                    })
                    continue

                new_line_zh = ""
                new_line_en = ""
                new_idx_element_start = pre_merged_mapping[0]["idx_element_start"]
                new_idx_element_end = pre_merged_mapping[-1]["idx_element_end"]
                new_pos = self._i18n_by_passage[passage_title][pre_merged_mapping[0]["idx_line"]]["pos"]
                for idx, mapping in enumerate(pre_merged_mapping):
                    new_line_en = f"{new_line_en}{mapping['line_en']}"
                    new_line_zh = f"{new_line_zh}{mapping['line_zh']}"

                    if idx == len(pre_merged_mapping) - 1:
                        continue

                    filling_start = self._i18n_by_passage[passage_title][mapping["idx_line"]]["pos"] + len(mapping["line_en"])
                    filling_end = self._i18n_by_passage[passage_title][pre_merged_mapping[idx+1]["idx_line"]]["pos"]
                    new_line_zh = f"{new_line_zh}{self._all_passages_by_passage[passage_title]['passage_text'][filling_start:filling_end]}"
                    new_line_en = f"{new_line_en}{self._all_passages_by_passage[passage_title]['passage_text'][filling_start:filling_end]}"

                merged_mappings_by_passage[passage_title].append({
                    "pos": new_pos,
                    "passage_title": passage_title,
                    "line_en": new_line_en,
                    "line_zh": new_line_zh,
                    "idx_element_start": new_idx_element_start,
                    "idx_element_end": new_idx_element_end,
                })

        with open("merged_mappings_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(merged_mappings_by_passage, fp, ensure_ascii=False, indent=2)
        self._merged_mappings_by_passage = merged_mappings_by_passage

    def replace(self):
        """将旧汉化文本替换成新汉化文本，即按行分隔替换成按元素分隔"""
        converted_i18n = {
            "typeB": {
                "TypeBOutputText": self._i18n["typeB"]["TypeBOutputText"],
                "TypeBInputStoryScript": []
            }
        }
        converted_i18n_by_passage = {}
        for passage_title, mappings in self._merged_mappings_by_passage.items():
            converted_i18n_by_passage[passage_title] = []
            for idx, mapping in enumerate(mappings):
                element_pos_start = self._all_elements_by_passage[passage_title][mapping["idx_element_start"]]["pos_start"]
                element_pos_end = self._all_elements_by_passage[passage_title][mapping["idx_element_end"]]["pos_end"]
                text_elements_en = self._all_passages_by_passage[passage_title]["passage_text"][element_pos_start:element_pos_end]

                line_pos_start = mapping["pos"]
                line_pos_end = mapping["pos"] + len(mapping["line_en"])
                text_line_en = mapping["line_en"]

                text_line_zh = mapping["line_zh"]
                text_elements_zh = (
                    f"{self._all_passages_by_passage[passage_title]['passage_text'][element_pos_start:line_pos_start]}"
                    f"{text_line_zh}"
                    f"{self._all_passages_by_passage[passage_title]['passage_text'][line_pos_end:element_pos_end]}"
                )

                i18n_data = {
                    "f": text_elements_en,
                    "t": text_elements_zh,
                    "pos": element_pos_start,
                    "fileName": self._i18n_by_passage[passage_title][0]["fileName"],
                    "pN": passage_title,
                }
                converted_i18n["typeB"]["TypeBInputStoryScript"].append(i18n_data)
                converted_i18n_by_passage[passage_title].append(i18n_data)

        with open("converted_i18n.json", "w", encoding="utf-8") as fp:
            json.dump(converted_i18n, fp, ensure_ascii=False, indent=2)
        self._converted_i18n = converted_i18n

        with open("converted_i18n_by_passage.json", "w", encoding="utf-8") as fp:
            json.dump(converted_i18n_by_passage, fp, ensure_ascii=False, indent=2)
        self._converted_i18n_by_passage = converted_i18n_by_passage


if __name__ == '__main__':
    from sugarcube2_localization.config import DIR_RESOURCES
    start = time.time()

    update = UpdateParse()
    update.read_data()
    update.get_mappings_before_update()
    update.merge()
    update.replace()

    end = time.time()
    logger.info(f"{end - start}s")
    Toaster(
        title="汉化映射",
        body=(
            "映射完毕啦！"
            "\n"
            f"耗时 {end-start:.2f}s"
        ),
        logo=DIR_RESOURCES / "img" / "dol-chs.ico"
    ).notify()