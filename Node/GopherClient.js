const net = require('net');

const CRLF = '\r\n';

class GopherMenuItem {
    constructor(type, selector, display, server, port, size = null, last_modified = null) {
        this.type = type;
        this.selector = selector;
        this.display = display;
        this.server = server;
        this.port = parseInt(port, 10);
        this.size = size; // Approximate size for Gopher+
        this.last_modified = last_modified;
    }
}

class GopherMenu {
    constructor() {
        this.items = [];
    }

    addItem(item) {
        if (item instanceof GopherMenuItem) {
            this.items.push(item);
        } else {
            throw new Error("Invalid item. Must be an instance of GopherMenuItem.");
        }
    }

    removeItem(item) {
        const index = this.items.indexOf(item);
        if (index > -1) {
            this.items.splice(index, 1);
        }
    }

    findItem(selector) {
        return this.items.find(item => item.selector === selector);
    }
}

class GopherClient {
    constructor(host, port) {
        this.host = host;
        this.port = port;
    }

    fetch(selector, binary = false, save = false) {
        // Download the selected item (binary/text etc.), handle save operation here
    }

    query(selector, query) {
        // Send a query to the gopher server
    }

    fetchMenu(selector) {
        return new Promise((resolve, reject) => {
            const socket = net.connect(this.port, this.host, () => {
                socket.write(selector + CRLF);
            });

            let dataBuffer = '';

            socket.on('data', (data) => {
                dataBuffer += data.toString();

                // If we detect the end of the Gopher menu (a period on a new line by itself),
                // we can process and resolve the promise.
                if (dataBuffer.endsWith(CRLF + '.' + CRLF)) {
                    const menuItems = this.processMenuData(dataBuffer);
                    resolve(menuItems);
                }
            });

            socket.on('error', (error) => {
                reject(error);
            });

            socket.on('close', () => {
                if (!dataBuffer.endsWith(CRLF + '.' + CRLF)) {
                    reject(new Error('Connection closed before full data received.'));
                }
            });
        });
    }

    processMenuData(data) {
        const menu = new GopherMenu();
    
        data.split(CRLF)
            .filter(line => line && line !== '.')
            .forEach(line => {
                const [type, rest] = [line[0], line.slice(1)];
                const [selector, display, server, port] = rest.split('\t');
                const menuItem = new GopherMenuItem(type, selector, display, server, port);
                menu.addItem(menuItem);
            });
    
        return menu;
    }

    updateMenu(menu) {
        // Update the menu, adding the old menu to the history, and regenerating the rendering of the item table.
    }
}

module.exports = GopherClient;
