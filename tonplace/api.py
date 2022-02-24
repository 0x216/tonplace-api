import json
from aiohttp import ClientSession
from typing import Any, Optional
from .errors import TonPlaceError
from aiohttp_socks import ProxyConnector


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
        if json_response.get("code") == "fatal":
            if self.return_error:
                return await response.text()
            raise TonPlaceError(
                f"Request error - {json_response.get('message')}"
            )
        return json_response
    
    
    async def get_me(self):
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


    async def close(self):
        if isinstance(self.session, ClientSession) and not self.session.closed:
            await self.session.close()