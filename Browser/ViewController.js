const gopherTypeDescriptions = {
    '0': 'Text',
    '1': 'Menu',
    '2': 'CSO',
    '3': 'Error',
    '4': 'BinHex',
    '5': 'DOS Bin',
    '6': 'UUencode',
    '7': 'Search',
    '8': 'Telnet',
    '9': 'Binary',
    'g': 'GIF',
    'I': 'Image',
    's': 'Sound',
    'i': 'Info',
    // ... add other types as needed
};

function getDescriptionForType(typeChar) {
    return gopherTypeDescriptions[typeChar] || 'Unknown';
}

class ViewController {
    constructor() {
        // Cache references to elements for performance
        this.fileTableBody = document.getElementById('fileTableBody');
        this.commandPrompt = document.getElementById('commandPrompt');
        this.submitCommandBtn = document.getElementById('submitCommand');
        
        // Set up event listeners
        this.submitCommandBtn.addEventListener('click', this.processCommand.bind(this));
        this.commandPrompt.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                this.processCommand();
                event.preventDefault();  // prevent default behavior, such as form submission
            }
        });
    }
    
    processCommand() {
        let line = this.commandPrompt.value;
        this.commandPrompt.value = '';
    
        if (line.trim() == "") return;

        if (line.startsWith('/')) {
            let parts = line.split(' ');
    
            switch(parts[0]) {
                case '/hop':
                    if (parts.length >= 3) {
                        let host = parts[1];
                        let port = parseInt(parts[2], 10);
    
                        window.gopherAPI.hop(host, port); 
                        
                        window.gopherAPI.scan('')
                            .then(menuItems => {
                                this.updateMenu(menuItems);
                            })
                            .catch(error => {
                                console.error("Error fetching menu:", error);
                            });                        
                    } else {
                        console.error("Invalid hop command. Format: /hop servername port");
                    }
                    break;
    
                // You can add more commands here in the future
                default:
                    console.error("Unknown command:", parts[0]);
            }
        } else {
            window.assistantAPI.processInput(line); 
        }
    }

    updateMenu(menu_items) {
        // Clear the current content of the table body
        this.fileTableBody.innerHTML = '';

        // For each menu item, create a new row and add it to the table
        for (let item of menu_items) {
            let row = document.createElement('tr');

            // Storing additional information needed
            row.dataset.type = item.type;
            row.dataset.host = item.host;
            row.dataset.port = item.port;
            row.dataset.selector = item.selector;

            // Adding a click listener to handle item clicks.
            row.addEventListener('click', (event) => {
                this.handleRowClick(event.currentTarget);
            });
            let typeCell = document.createElement('td');
            // Convert between item type and descriptor
            typeCell.textContent = getDescriptionForType(item.type);
            row.appendChild(typeCell);

            let itemCell = document.createElement('td');
            itemCell.textContent = item.name;
            row.appendChild(itemCell);

            let descCell = document.createElement('td');
            descCell.textContent = item.description || '';  // Using empty string as fallback if no description
            row.appendChild(descCell);

            this.fileTableBody.appendChild(row);
        }
    }
    handleRowClick(row) {
        const type = row.dataset.type;
        const host = row.dataset.host;
        const port = parseInt(row.dataset.port, 10);
        const selector = row.dataset.selector;
    

        switch (type) {
            // Handle based on the item type
            case "1": 
                if (window.gopherAPI.currentHost() !== host || window.gopherAPI.currentPort() !== port) {
                    window.gopherAPI.hop(host, port);
                }

                window.gopherAPI.scan(selector)
                .then(menuItems => {
                    this.updateMenu(menuItems);
                })
                .catch(error => {
                    console.error("Error fetching menu for selector:", selector, "Error:", error);
                });
                break;
            //... add other cases as needed
        }
    }
}