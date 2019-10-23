from db import Db
import aiohttp
import asyncio
import random
import requests
import time


class Proxy(Db):
    async def proxy_init(self):
        self.proxylist = await self.db_proxies_load()

    async def proxy_rnd(self):
        return self.proxylist[random.randint(0, len(self.proxylist)-1)]

    async def proxy_clear(self):
        self.proxylist = []
        await self.db_proxies_clear()

    async def proxy_update(self):
        response = requests.get('https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list')
        if response.status_code == 200:
            null = None
            self.proxylist = list(eval(response.text.replace('\n', ',')))
            sem = asyncio.Semaphore(1000)
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(*[self.proxy_check(sem, session, proxy) for proxy in self.proxylist])
        else:
            raise

    async def proxy_check(self, sem, session, proxy):
        async with sem:
            proxy['url'] = f'http://{proxy["host"]}:{proxy["port"]}'
            try:
                async with session.get('https://m.avito.ru', proxy=proxy['url'], timeout=2, ssl=False) as response:
                    if response.status == 200:
                        print(proxy)
                        await self.db_proxy_save(proxy)
            except:
                pass
