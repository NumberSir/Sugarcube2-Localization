from abc import ABC, abstractmethod
from typing import Sequence
from urllib.parse import quote

import httpx
from lxml import etree

from sugarcube2_localization.config import settings


class BaseCredits(ABC):
	def __init__(self, client: httpx.AsyncClient):
		self._client = client

	@abstractmethod
	async def get_credit_members(self, *args, **kwargs) -> Sequence[str]:
		raise NotImplementedError

	@property
	def client(self) -> httpx.AsyncClient:
		return self._client


class ParatranzCredits(BaseCredits):
	async def get_credit_members(self, project_id: int = settings.paratranz.project_id) -> Sequence[str]:
		response = await self._get_members_response(project_id)
		return self._filter_scored_members(response.json())

	async def _get_members_response(self, project_id: int = settings.paratranz.project_id) -> httpx.Response:
		"""项目所有成员信息"""
		url = f"https://paratranz.cn/api/projects/{project_id}/members"
		headers = {"Authorization": settings.paratranz.token, "user-agent": settings.project.user_agent}
		return await self.client.get(url, headers=headers)

	@staticmethod
	def _filter_scored_members(response_members: list[dict]) -> list[str]:
		"""筛选出有贡献值的成员"""
		return sorted([
			f'{member["user"]["username"]}({member["user"]["nickname"]})'
			if member["user"].get("nickname")
			else f'{member["user"]["username"]}'
			for member in response_members
			if member["totalPoints"]
		])


class MirahezeCredits(BaseCredits):
	async def get_credit_members(self, limit: int = settings.mediawiki.user_list_limit) -> Sequence[str]:
		response = await self._get_members_response(limit)
		return self._filter_scored_members(response.text)

	async def _get_members_response(self, limit: int = settings.mediawiki.user_list_limit) -> httpx.Response:
		"""项目所有成员信息"""
		url = f"https://degreesoflewditycn.miraheze.org/wiki/{quote('特殊:用户列表')}"
		params = {
			"editsOnly"       : 1,
			"wpFormIdentifier": "mw-listusers-form",
			"limit"           : limit,
		}
		headers = {"user-agent": settings.project.user_agent}
		return await self.client.get(url, params=params, headers=headers)

	@staticmethod
	def _filter_scored_members(html: str) -> list[str]:
		html = etree.HTML(html)
		return sorted(_ for _ in html.xpath("//bdi/text()") if _.strip())


class GitHubCredits(BaseCredits):
	async def get_credit_members(self, limit: int = settings.mediawiki.user_list_limit) -> Sequence[str]:
		response = await self._get_members_response(limit)
		return self._filter_scored_members(response.text)

	async def _get_members_response(self, limit: int = settings.mediawiki.user_list_limit) -> httpx.Response:
		"""项目所有成员信息"""
		url = f"https://degreesoflewditycn.miraheze.org/wiki/{quote('特殊:用户列表')}"
		params = {
			"editsOnly"       : 1,
			"wpFormIdentifier": "mw-listusers-form",
			"limit"           : limit,
		}
		headers = {"user-agent": settings.project.user_agent}
		return await self.client.get(url, params=params, headers=headers)

	@staticmethod
	def _filter_scored_members(html: str) -> list[str]:
		html = etree.HTML(html)
		return sorted(_ for _ in html.xpath("//bdi/text()") if _.strip())


class DiscordCredits:
	async def get_issue_contributors(self):
		"""bug fixes & translation enhancements"""

	async def announce(self):
		"""@everyone"""
		