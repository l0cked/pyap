from db import Db
from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal
import aiohttp
import asyncio
import requests
import time


class ProxyObject(QObject):
    message = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def run(self):
        asyncio.run(self.update())

    async def update(self):
        response = requests.get('https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list')
        if response.status_code == 200:
            null = None
            self.proxylist = list(eval(response.text.replace('\n', ',')))
            sem = asyncio.Semaphore(1000)
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(*[self.check(sem, session, proxy) for proxy in self.proxylist])
        else:
            raise
        self.finished.emit()

    async def check(self, sem, session, proxy):
        async with sem:
            proxy['url'] = f'http://{proxy["host"]}:{proxy["port"]}'
            try:
                async with session.get('https://m.avito.ru', proxy=proxy['url'], timeout=2, ssl=False) as response:
                    if response.status == 200:
                        self.message.emit({'proxy': proxy})
            except:
                pass


class Proxy(Db):
    async def proxy_init(self):
        self.proxylist = await self.db_proxies_load()

    async def proxy_clear(self):
        self.proxylist = []
        await self.db_proxies_clear()

    def proxy_update(self):
        self.proxy_thread = QThread()

        self.proxy_obj = ProxyObject()
        self.proxy_obj.moveToThread(self.proxy_thread)
        self.proxy_obj.message.connect(self.proxy_on_message)
        self.proxy_obj.finished.connect(self.proxy_on_finished)

        self.proxy_thread.started.connect(self.proxy_obj.run)
        self.proxy_thread.start()

    def proxy_on_message(self, message):
        proxy = message['proxy']
        print(proxy)
        self.loop.run_until_complete(self.db_proxy_save(proxy))

    def proxy_on_finished(self):
        self.proxy_thread.quit()
        self.proxy_thread.wait()
