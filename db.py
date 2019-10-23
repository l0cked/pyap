from datetime import datetime
from utils import Utils
import aiosqlite


class Db(Utils):
    async def db_init(self):
        self.db = await aiosqlite.connect('pyap.db')
        self.db.row_factory = self.db_dict_factory
        await self.db.executescript('''
            CREATE TABLE IF NOT EXISTS products (
                id integer PRIMARY KEY,
                added datetime,
                product_id integer,
                url text NOT NULL UNIQUE,
                title text,
                price text,
                address text,
                description text,
                author text,
                phone text
            );
            CREATE TABLE IF NOT EXISTS proxies (
                id integer PRIMARY KEY,
                url text NOT NULL UNIQUE
            );
            ''')
        await self.db.commit()
        self.db_products_lenght = await self.db_get_products_length()

    async def db_close(self):
        await self.db.close()

    def db_dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    async def db_get_products_length(self):
        cursor = await self.db.execute('SELECT COUNT(*) FROM products')
        res = await cursor.fetchone()
        return res['COUNT(*)']

    async def db_product_save(self, product):
        if 'phone' in product and 'author' in product:
            if len(product['phone']) == 11 and product['author'] != '':
                await self.db.execute('INSERT OR IGNORE INTO products (added,product_id,url,title,price,address,description,author,phone) VALUES (?,?,?,?,?,?,?,?,?)',
                    (datetime.now(), product['id'], product['url'], product['title'], product['price'], product['address'], product['desc'], product['author'], product['phone']))
                await self.db.commit()

    async def db_proxy_save(self, proxy):
        await self.db.execute('INSERT OR IGNORE INTO proxies (url) VALUES (?)', (proxy['url'],))
        await self.db.commit()

    async def db_proxies_load(self):
        cursor = await self.db.execute('SELECT * FROM proxies')
        return await cursor.fetchall()

    async def db_proxies_clear(self):
        await self.db.execute('DELETE FROM proxies')
        await self.db.commit()
