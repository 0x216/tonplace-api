import io
import json
from tenacity import retry, wait_fixed, stop_after_delay, stop_after_attempt
from aiohttp import ClientSession
from typing import Any, Union, Optional

import aiohttp
from .errors import TonPlaceError
from aiohttp_socks import ProxyConnector

from tonplace.attachments import Attachments

BASE_API = "https://api.ton.place/"

class API:
    def __init__(self,
            token: str, 
            proxy: Optional[str] = None):
        self.base_path = BASE_API
        self.token = token
        self.proxy = proxy
        self.connector = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Authorization": token,  
        }
        if self.proxy:
            self.connector = ProxyConnector.from_url(self.proxy)
        self.session = ClientSession(headers=self.headers,
                                    connector=self.connector)

    @retry(wait=wait_fixed(60), stop=(stop_after_delay(30) | stop_after_attempt(20)))
    async def request(
        self,
        method: str,
        path: str,
        data: Optional[Any] = None,
        json_data: Optional[dict] = None,
    ):
        response = await self.session.request(
            method=method,
            url = BASE_API + path,
            data=data,
            json=json_data,
        )
        
        if response.status >= 500:
            raise TonPlaceError('Site is down')
        try:
            json_response = json.loads(await response.text())
        except json.JSONDecodeError:
            raise TonPlaceError(await response.text())
        if isinstance(json_response, str):
            return json_response
        if json_response.get("code") == "fatal" or 'access_token':
            if self.return_error:
                return await response.text()
            raise TonPlaceError(
                f"Request error - {json_response.get('message')}"
            )
        return json_response
    
    
    async def get_me(self):
        """
        Info about yourself
        """
        user = await self.request("POST", path="main/init")
        return user

    async def get_user(self, user_id: int):
        """
        User info
        :param user_id:
        :return:
        """
        user = await self.request("POST", path=f"profile/{user_id}")
        return user

    async def get_group(self, group_id: int):
        """
        Group info
        :param group_id:
        :return:
        """
        user = await self.request("POST", path=f"group/{group_id}")
        return user

    async def search(
        self,
        tab: str,
        sort: str = "popular",
        query: str = "",
        city: int = 0,
        start_from: int = 0,
    ):
        """
        Search (return 30 elements)
        :param tab: explore|peoples|groups
        :param sort: popular|new|online
        :param query: search query
        :param start_from: offset
        :param city: default zero
        :return:
        """
        result = await self.request(
            "POST",
            path=f"search",
            json_data={
                "query": query,
                "startFrom": start_from,
                "tab": tab,
                "sort": sort,
                "city": city,
            },
        )
        return result

    async def follow(self, user_id: int):
        result = await self.request(
            "POST",
            path=f"follow/{user_id}/add",
        )
        return result

    async def unfollow(self, user_id: int):
        result = await self.request(
            "POST",
            path=f"follow/{user_id}/del",
        )
        return result

    async def like(self, post_id: int):
        result = await self.request(
            "POST",
            path=f"likes/{post_id}/post/add",
        )
        return result

    async def unlike(self, post_id: int):
        result = await self.request(
            "POST",
            path=f"likes/{post_id}/post/del",
        )
        return result

    async def write_comment(
        self,
        post_id: int,
        text: str = "",
        attachments: Optional[list] = None,
        reply: Optional[int] = 0,
        group_id: Optional[int] = 0,
    ):
        """
        :param post_id:
        :param text:
        :param attachments:
        :param reply: 
        :param group_id:
        :return:
        """
        if attachments is None:
            attachments = []
        if isinstance(attachments, Attachments):
            attachments = attachments.get_attachments()
        result = await self.request(
            "POST",
            path=f"posts/new",
            json_data={
                "parentId": post_id,
                "replyTo": reply,
                "text": text,
                "attachments": attachments,
                "groupId": group_id,
            },
        )
        return result

    async def read_post(self, post_id: int):
        """
        Increase views of post
        :param post_id:
        :return:
        """
        result = await self.read_posts([post_id])
        return result

    async def read_posts(self, post_ids: list[int]):
        """
        Increase views of posts
        :param post_ids:
        :return:
        """
        result = await self.request(
            "POST",
            path=f"posts/read",
            json_data={
                "posts": post_ids,
            },
        )
        return result

    async def get_post(self, post_id: int):
        # TODO: next from comments
        result = await self.request(
            "GET",
            path=f"posts/{post_id}",
        )
        return result

    async def get_feed(
        self, section: str, start_from: int = 0, suggestions: Optional[bool] = None
    ):
        """
        Get Feed
        :param section: - following|suggestions|liked (follows, suggetions, liked)
        :param start_from: - offset
        :param suggestions:
        :return:
        """
        if suggestions is None and section != "suggestions":
            suggestions = False

        result = await self.request(
            "POST",
            path=f"feed",
            json_data={
                "section": section,
                "startFrom": start_from,
                "suggestions": suggestions,
            },
        )
        return result

    async def get_dialogs(self):
        result = await self.request(
            "GET",
            path=f"im",
        )
        return result

    async def get_notify(self):
        result = await self.request(
            "GET",
            path=f"notify",
        )
        return result

    async def get_owned_groups(self):
        result = await self.request(
            "GET",
            path=f"groups",
        )
        return result

    async def get_balance(self):
        result = await self.request(
            "GET",
            path=f"balance",
        )
        return result

    async def send_ton(self, address: str, amount: float):
        result = await self.request(
            "POST",
            path=f"balance/withdraw",
            json_data={
                "address": address,
                "amount": amount,
            },
        )
        return result

    async def create_post(
        self,
        owner_id: int,
        text: str = "",
        parent_id: int = 0,
        timer: int = 0,
        attachments: Optional[Union[list, Attachments]] = None,
    ):
        """
        Create post
        :param owner_id: id of page or group (group id must be negative 123 -> -123)
        :param text:
        :param parent_id:
        :param timer:
        :param attachments:
        :return:
        """
        if attachments is None:
            attachments = []
        if isinstance(attachments, Attachments):
            attachments = attachments.get_attachments()

        result = await self.request(
            "POST",
            path=f"posts/new",
            json_data={
                "ownerId": owner_id,
                "text": text,
                "parentId": parent_id,
                "attachments": attachments,
                "timer": timer,
            },
        )
        return result

    async def _upload(
        self,
        upload_type: str,
        data: bytes,
        content_type: str,
        album_id: int = -3,
        file_name: str = "blob",
    ):
        """
        :param upload_type: photos|video
        :param data:
        :param content_type:
        :param album_id:
        :param file_name:
        :return:
        """
        headers = self.headers.copy()

        form_data = aiohttp.FormData()
        form_data.add_field(
            "file", io.BytesIO(data), filename=file_name, content_type=content_type
        )
        form_data.add_field("album_id", str(album_id))
        form_data = form_data()
        headers.update(form_data.headers)

        resp = await self.session.post(
            f"https://upload.ton.place/{upload_type}/upload",
            headers=headers,
            data=form_data,
        )

        return json.loads(await resp.text())

    async def upload_photo(
        self, data: bytes, album_id: int = -3, file_name: str = "blob"
    ):
        return await self._upload(
            upload_type="photos",
            data=data,
            content_type="image/jpeg",
            album_id=album_id,
            file_name=file_name,
        )

    async def upload_video(
        self, data: bytes, album_id: int = -3, file_name: str = "blob"
    ):
        return await self._upload(
            upload_type="video",
            data=data,
            content_type="video/mp4",
            album_id=album_id,
            file_name=file_name,
        )

    async def get_referrals(self):
        result = await self.request(
            "GET",
            path=f"invite/friends",
        )
        return result

    async def edit_profile(
        self,
        birth_day: int,
        birth_month: int,
        birth_year: int,
        city_id: int,
        country_id: int,
        first_name: str,
        last_name: str,
        sex: int,
    ):
        result = await self.request(
            "POST",
            path=f"profile/edit",
            json_data={
                "bDay": birth_day,
                "bMonth": birth_month,
                "bYear": birth_year,
                "cityId": city_id,
                "countryId": country_id,
                "firstName": first_name,
                "lastName": last_name,
                "sex": sex,
            },
        )
        return result

    async def check_domain(self, domain: str):
        """
        Is domain free
        :return:
        """
        result = await self.request(
            "GET", path=f"domain/check", json_data={"domain": domain}
        )
        return result

    async def change_domain(self, domain: str):
        result = await self.request(
            "GET", path=f"profile/domain", json_data={"domain": domain}
        )
        return result

    async def get_follow(
        self,
        user_id: int,
        followers_type: str = "inbox",
        start_from: int = 0,
        query: str = "",
    ):
        """
        :param user_id:
        :param query:
        :param start_from:
        :param followers_type: inbox|outbox (followers|following)
        :return:
        """
        result = await self.request(
            "GET",
            path=f"followers/{user_id}/more",
            json_data={
                "query": query,
                "type": followers_type,
                "startFrom": start_from,
            },
        )
        return result

    async def close(self):
        await self.session.close()