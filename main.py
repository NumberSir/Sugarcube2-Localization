import asyncio
import time

import httpx

from src.tools.paratranz import Paratranz
from src.config import settings
from src.log import logger
from src.toast import Toaster


async def main():
    start = time.time()
    async with httpx.AsyncClient() as client:
        paratranz = Paratranz(client)
        await paratranz.download()
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