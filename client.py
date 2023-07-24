import asyncio
import curses
import os

class GopherClient:
    ITEM_TYPES = {
        "0": "(TEXT)",
        "1": "(DIR)",
        "9": "(BIN))",
        "I": "(IMAGE)",
        "<": "(SOUND)",
        ";": "(VIDEO)",
        "d": "(DOC)",
        "h": "(HTML)",
        '7': "(SEARCH)",
    }

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.menu = []
        self.menu_history = []  # stack to store menu history
        self.selected_item = 0
        self.last_query = ['', None]  # to store last query for re-fetching

    async def fetch(self, type, selector, query=None):
        self.last_query = [selector, query]
        reader, writer = await asyncio.open_connection(self.host, self.port)
        if query is not None:
            message = selector + '\t' + query + "\r\n"
        else:
            message = selector + "\r\n"
        writer.write(message.encode('utf-8'))
        await writer.drain()

        temp_menu = []  # temporary menu to store fetched items
        item_info = None
        while True:
            line = await reader.readline()
            if not line or line == b'.':
                break
            line = line.decode('utf-8').rstrip()
            if line.startswith('+INFO: '):
                item_info = line[7:].split('\t')
            else:
                parts = line.split('\t')
                item = [parts[0][0], parts[0][1:]] + parts[1:]
                if item_info is not None:
                    item.extend(item_info)

                item_info = None
                temp_menu.append(item)

        if temp_menu:  # if the fetched menu is not empty
            self.menu = temp_menu  # set current menu to the fetched menu
            self.menu_history.append(self.menu)  # add fetched menu to the history

        writer.close()
        await writer.wait_closed()

    def render(self, stdscr):
        while True:

            stdscr.clear()

            for i, item in enumerate(self.menu):
                if i == self.selected_item:
                    stdscr.attron(curses.A_REVERSE)

                filetype = self.ITEM_TYPES.get(item[0])
                if filetype is None:
                    filetype = "(UNKNOWN)"
                filename = item[1]
                description = item[2]
                size = item[9] if item[9] != "-1" else ""
                timestamp = item[10] if item[10] else ""
                stdscr.addstr(i, 0, f'{filetype} {filename} {size} {timestamp} {description}'.strip())

                if i == self.selected_item:
                    stdscr.attroff(curses.A_REVERSE)
            stdscr.refresh()

            key = stdscr.getch()

            if key == curses.KEY_UP and self.selected_item > 0:
                self.selected_item -= 1
            elif key == curses.KEY_DOWN and self.selected_item < len(self.menu) - 1:
                self.selected_item += 1
            elif key == curses.KEY_RIGHT or key == curses.KEY_ENTER or key in [10, 13]:
                dt = self.menu[self.selected_item][0]
                if dt != '7':
                    asyncio.run(self.fetch(dt, self.menu[self.selected_item][2]))
                else:
                    stdscr.addstr(len(self.menu)+2, 0, 'Enter your search:')
                    curses.echo()
                    query = stdscr.getstr(len(self.menu)+3, 0, 20)
                    curses.noecho()
                    asyncio.run(self.fetch(dt, self.menu[self.selected_item][2], query.decode('utf-8')))
                self.selected_item = 0  # reset selected item
            elif key == curses.KEY_LEFT:  # back to previous menu
                if len(self.menu_history) > 1:  # ensure that we have a history to go back to
                    self.menu_history.pop()  # remove current menu from history
                    self.menu = self.menu_history[-1]  # set menu to last menu in history
                    self.selected_item = 0  # reset selected item
            elif key == ord('r') and (curses.KEY_CTRL & 0x1f):  # re-fetch menu (Ctrl+R)
                selector, query = self.last_query
                asyncio.run(self.fetch(dt, selector, query))
                self.selected_item = 0  # reset selected item

gc = GopherClient('localhost', 10070)
asyncio.run(gc.fetch('1', ''))
curses.wrapper(gc.render)
