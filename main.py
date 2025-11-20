import asyncio
import time

import httpx

from sugarcube2_localization.tools.paratranz import Paratranz
from sugarcube2_localization.config import settings
from sugarcube2_localization.log import logger
from sugarcube2_localization.toast import Toaster

from sugarcube2_localization.core.parser.twee3 import Twee3Parser
from sugarcube2_localization.core.reviewer.twee3 import Twee3Reviewer
from sugarcube2_localization.core.parser.javascript import JavaScriptParser
from sugarcube2_localization.core.reviewer.javascript import JavascriptReviewer


async def main():
    start = time.time()
    # async with httpx.AsyncClient() as client:
    #     paratranz = Paratranz(client)
    #     await paratranz.download()

    """twee3"""
    twee3parser = Twee3Parser()
    twee3reviewer = Twee3Reviewer()
    twee3parser.get_all_elements_info(is_old_macro=True)
    twee3reviewer.validate_all_elements()
    """js"""
    jsparser = JavaScriptParser()
    jsparser.tokenize()
    jsreviewer = JavascriptReviewer()
    jsreviewer.validate_basic_syntax()

    end = time.time()
    return end - start


if __name__ == '__main__':
    last = asyncio.run(main())
    logger.info(f"===== 总耗时 {last or -1:.2f}s =====")

    Toaster(
        title="DoL 汉化脚本",
        body=(
            "DoL 汉化脚本运行完啦"
            "\n"
            f"耗时 {last or -1:.2f}s"
        ),
        logo=settings.filepath.resources / "img" / "dol-chs.ico"
    ).notify()