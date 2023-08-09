const net = require('net');
const querystring = require('querystring');

const CRLF = '\r\n';

class GopherMenuItem {
    constructor(type, name, selector, host, port, description = null, mime = null, size = null, modified = null) {
        this.type = type;
        this.name = name;
        this.selector = selector;
        this.host = host;
        this.port = parseInt(port, 10);
        this.description = description;
        this.mime = mime;
        this.size = size;
        this.modified = modified;
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

    // Make class iterable
    *[Symbol.iterator]() {
        for (const item of this.items) {
            yield item;
        }
    }}

class GopherClient {
    constructor(host, port) {
        this.host = host;
        this.port = port;
    }

    setServer(host, port) {
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
                if (dataBuffer.endsWith(CRLF + '.')) {
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
        const extractField = (field, str) => {
            const prefix = `+${field.toUpperCase()}:`;
            if (str.startsWith(prefix)) {
                return str.substring(prefix.length).trim();
            } else {
                throw new Error(`Invalid ${field} field format.`);
            }
        };
    
        data.split(CRLF)
            .filter(line => line && line !== '.')
            .forEach(line => {
                const [type, rest] = [line[0], line.slice(1)];
                const parts = rest.split('\t');
    
                const name = querystring.unescape(parts[0]);
                const selector = parts[1];
                const host = parts[2];
                const port = parts[3];
                let description = null, mime = null, size = null, modified = null;
    
                if (parts.length > 4) {
                    if (parts.length < 8) {
                        throw new Error("Expected either the basic format or all four additional fields in the correct order.");
                    }
                    
                    description = querystring.unescape(extractField('DESCRIPTION', parts[4]));
                    mime = extractField('MIME', parts[5]);
                    size = extractField('SIZE', parts[6]);
                    modified = extractField('MODIFIED', parts[7]);
                }    
                const menuItem = new GopherMenuItem(type, name, selector, host, port, description, mime, size, modified);
                menu.addItem(menuItem);
            });
    
        return menu;
    }
}

module.exports = GopherClient;
