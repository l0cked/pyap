from parse import Parse
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QStyle, QMenu
import asyncio
import webbrowser


class Main(QSystemTrayIcon, Parse):
    app = QApplication([])
    loop = asyncio.get_event_loop()

    def __init__(self):
        super().__init__()
        self.setIcon(QIcon('http/favicon.ico'))
        menu = QMenu()
        browserAction = menu.addAction('Open control panel')
        browserAction.triggered.connect(self.browserClicked)
        menu.addSeparator()
        parseAction = menu.addAction('Parse')
        parseAction.triggered.connect(self.parseClicked)
        menu.addSeparator()
        proxyUpdateAction = menu.addAction('Proxylist update')
        proxyUpdateAction.triggered.connect(self.proxyUpdateClicked)
        proxyClearAction = menu.addAction('Proxylist clear')
        proxyClearAction.triggered.connect(self.proxyClearClicked)
        menu.addSeparator()
        quitAction = menu.addAction('Quit')
        quitAction.triggered.connect(self.quitClicked)
        self.setContextMenu(menu)

        self.loop.run_until_complete(self.start())

        self.show()
        self.app.exec_()

        self.loop.run_until_complete(self.stop())

    async def start(self):
        await self.db_init()
        await self.proxy_init()

    async def stop(self):
        await self.db_close()

    def browserClicked(self):
        webbrowser.open('http://192.168.1.37:80', new=2)

    def parseClicked(self):
        self.parse_update()

    def proxyUpdateClicked(self):
        self.proxy_update()

    def proxyClearClicked(self):
        self.loop.run_until_complete(self.proxy_clear())

    def quitClicked(self):
        self.hide()
        self.app.exit()

Main()
