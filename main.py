import asyncio
from weakref import proxy

import aiohttp
from tonplace import API, get_token
from aiohttp import ClientSession
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector

async def main():
    
 
    token = 'OAzZsgL163ChwL2fc87geeTeYhM71RQf1uUjjSQkWRgB2OBrVq4HZ8LW6jsyK0YV'
    proxy = 'socks5://W1Ekbv:N8amFN@181.177.87.217:9220'
    token = await get_token("+79162098868", save_session=True,
    proxy=proxy,
    timeout=10)
    api = API(token=token, proxy=proxy)
    print(await api.get_me())
    print(await api.get_user(1))
    me = await api.get_me()
    myid = me['user']['id']
    followed = me['user']['followed']
 #   for i in range(0, followed, 30):
 #       users = await api.get_follow(myid, start_from=i, followers_type="outbox")
 #       for user in range(len(users)):
 #           print(user)
    await api.close()

    

loop = asyncio.get_event_loop()
loop.run_until_complete(main())