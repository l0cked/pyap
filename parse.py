from lxml import html
from proxy import Proxy
from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal
import aiohttp
import asyncio
import random
import time


class ParseObject(QObject):
    message = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    info = {'time': time.time()}

    def __init__(self, proxylist):
        super().__init__()
        self.proxylist = proxylist

    @pyqtSlot()
    def run(self):
        asyncio.run(self.update())

    async def update(self):
        self.sem = asyncio.Semaphore(100)

        locations = [
            'rossiya',
            'moskva',
            'odintsovo',
            'lesnoy_gorodok',
            'golitsyno',
            'gorki-10',
            'zvenigorod',
            'kokoshkino',
            'moskovskaya_oblast_krasnoznamensk',
            'novoivanovskoe'
        ]

        categories = [
            'avtomobili',
            'kvartiry',
            'lichnye_veschi',
            'bytovaya_elektronika'
        ]

        urls = []
        for location in locations:
            urls.append(f'https://m.avito.ru/{location}?owner[]=private&sort=date')
            for category in categories:
                urls.append(f'https://m.avito.ru/{location}/{category}?owner[]=private&sort=date')
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*[self.get_product_urls(session, url) for url in urls])

        self.info['time'] = time.time()-self.info['time']
        self.finished.emit(self.info)

    async def fetch(self, session, url):
        async with self.sem:
            try:
                proxy = await self.proxy_rnd()
                async with session.get(url, proxy=proxy['url'], timeout=5, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
            except:
                pass
            return False

    async def get_product_urls(self, session, url):
        text = await self.fetch(session, url)
        if text:
            dom = html.fromstring(text)
            urls = dom.xpath('//a[@data-marker="item/link"]/@href')
            print('Found product urls:', len(urls))
            await asyncio.gather(*[self.get_product(session, 'https://m.avito.ru' + url, url.split('_')[-1]) for url in urls])
        else:
            print('ERROR GET CATEGORY HTML:', url)

    async def get_product(self, session, product_url, product_id):
        product = {
            'id': product_id,
            'url': product_url
        }
        text = await self.fetch(session, f'https://m.avito.ru/api/1/items/{product["id"]}/phone?key=af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir')
        if text:
            product['phone'] = text.split('%2B')[-1].split('"')[0]
            if len(product['phone']) == 11:
                product_text = await self.fetch(session, product['url'])
                if product_text:
                    dom = html.fromstring(product_text)
                    product.update({
                        'title':   self.list2str(dom.xpath('//h1[@data-marker="item-description/title"]/span/text()')),
                        'price':   self.list2str(dom.xpath('//span[@data-marker="item-description/price"]/text()')),
                        'address': self.list2str(dom.xpath('//span[@data-marker="delivery/location"]/text()')),
                        'desc':    self.list2str(dom.xpath('//div[@data-marker="item-description/full-text"]/text()')),
                        'author':  self.list2str(dom.xpath('//span[@data-marker="seller-info/name"]/text()'))
                    })
                else:
                    product['status'] = 'ERROR GET PRODUCT HTML'
            else:
                product['status'] = 'ERROR PHONE LEN'
                del product['phone']
        else:
            product['status'] = 'ERROR GET PHONE JSON'

        self.message.emit({'product': product})

    async def proxy_rnd(self):
        return self.proxylist[random.randint(0, len(self.proxylist)-1)]

    def list2str(self, l):
        if len(l) > 0:
            return l[0].strip()
        return ''


class Parse(Proxy):
    def parse_update(self):
        self.parse_thread = QThread()

        self.parse_obj = ParseObject(self.proxylist)
        self.parse_obj.moveToThread(self.parse_thread)
        self.parse_obj.message.connect(self.parse_on_message)
        self.parse_obj.finished.connect(self.parse_on_finished)

        self.parse_thread.started.connect(self.parse_obj.run)
        self.parse_thread.start()

    def parse_on_message(self, message):
        product = message['product']
        print(product)
        print('---')
        self.loop.run_until_complete(self.db_product_save(product))

    def parse_on_finished(self, info):
        print(info)
        self.parse_thread.quit()
        self.parse_thread.wait()
