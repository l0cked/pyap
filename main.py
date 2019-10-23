from lxml import html
from proxy import Proxy
import aiohttp
import asyncio


class Main(Proxy):
    counter_request = 0
    counter_request_ok = 0
    counter_error = 0

    def __init__(self):
        asyncio.run(self.start())

    async def fetch(self, session, url):
        self.counter_request += 1
        try:
            proxy = await self.proxy_rnd()
            async with self.sem:
                async with session.get(url, proxy=proxy['url'], timeout=5, ssl=False) as response:
                    if response.status == 200:
                        self.counter_request_ok += 1
                        return await response.text()
        except:
            self.counter_error += 1
            pass
        return False

    async def getProductUrls(self, session, url):
        text = await self.fetch(session, url)
        if text:
            dom = html.fromstring(text)
            urls = dom.xpath('//a[@data-marker="item/link"]/@href')
            print('Found product urls:', len(urls))
            await asyncio.gather(*[self.getProduct(session, 'https://m.avito.ru' + url, url.split('_')[-1]) for url in urls])
        else:
            print('ERROR GET CATEGORY HTML:', url)
            self.counter_error += 1

    async def getProduct(self, session, product_url, product_id):
        product = {
            'id': product_id,
            'url': product_url
        }
        text = await self.fetch(session, f'https://m.avito.ru/api/1/items/{product_id}/phone?key=af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir')
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
                    self.counter_error += 1
            else:
                product['status'] = 'ERROR PHONE LEN'
                self.counter_error += 1
                del product['phone']
        else:
            product['status'] = 'ERROR GET PHONE JSON'
            self.counter_error += 1

        await self.db_product_save(product)
        print(product)
        print('---')

    async def start(self):
        await self.db_init()
        # await self.proxy_clear()
        # await self.proxy_update()
        await self.proxy_init()

        self.sem = asyncio.Semaphore(100)

        cities = [
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
        for city in cities:
            for category in categories:
                urls.append(f'https://m.avito.ru/{city}/{category}?sort=date')
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*[self.getProductUrls(session, url) for url in urls])

        print(f'requests: {self.counter_request_ok}/{self.counter_request}')
        print('errors:', self.counter_error)
        print('new:', await self.db_get_products_length() - self.db_products_lenght)

        await self.db_close()


Main()
