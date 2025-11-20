import contextlib
import os
from zipfile import ZipFile
from enum import Enum, auto

import httpx

from sugarcube2_localization.config import settings, DIR_TMP

class Paratranz:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._base_url = "https://paratranz.cn/api"
        self._project_id = settings.paratranz.project_id

    async def download(self):
        os.makedirs(DIR_TMP, exist_ok=True)
        with contextlib.suppress(httpx.TimeoutException):
            await self._trigger_export()
        await self._download_artifacts()
        await self._extract_artifacts()

    async def _trigger_export(self):
        url = f"{self.base_url}/projects/{self._project_id}/artifacts"
        headers = {"Authorization": settings.paratranz.token}
        httpx.post(url, headers=headers, verify=False)

    async def _download_artifacts(self):
        url = f"{self.base_url}/projects/{self._project_id}/artifacts/download"
        headers = {"Authorization": settings.paratranz.token}
        content = (await self.client.get(url, headers=headers, follow_redirects=True)).content
        with (DIR_TMP / "paratranz_export.zip").open("wb") as fp:
            fp.write(content)

    async def _extract_artifacts(self):
        with ZipFile(DIR_TMP / "paratranz_export.zip") as zfp:
            zfp.extractall(settings.filepath.paratranz)

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def project_id(self) -> int:
        return self._project_id


class RequestMethod(Enum):
	GET = auto()
	HEAD = auto()
	DELETE = auto()
	POST = auto()
	PUT = auto()
	PATCH = auto()
	OPTIONS = auto()

class ParatranzApi:
	def __init__(self) -> None:
		...

	async def call_api(self, method: str = RequestMethod.GET.name, url: str = "", headers: dict = None, body: dict = None, params: dict = None, timeout: int = None):
		...


__all__ = [
    'Paratranz'
]
