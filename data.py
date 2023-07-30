import sqlite3

conn = None

# Initialize the database.
def init():
    global conn
    print("Initializing database...")
    conn = sqlite3.connect('gopher.db')  # You can replace 'my_database.db' with your preferred database name.
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS items
              (name TEXT, path TEXT, last_modified TEXT, item_type INTEGER, info TEXT,
               PRIMARY KEY(name, path))
              ''')
    conn.commit()

# Return None if no entry found.
def last_modified(name, path):
    global conn
    c = conn.cursor()
    c.execute("SELECT last_modified FROM items WHERE name=? AND path=?", (name, path))
    result = c.fetchone()
    if result is None:
        return None
    else:
        return result[0]

# Get the item info or None associated with name and path, if last_modified is None, else set the entry.
def item_info(name, path, last_modified=None, item_type=None, info=None):
    global conn
    c = conn.cursor()
    
    if last_modified is None:
        c.execute("SELECT info FROM items WHERE name=? AND path=?", (name, path))
        result = c.fetchone()
        conn.close()
        if result is None:
            return None
        else:
            return result[0]
    else:
        print(f"Adding new entry for {path}...\n==============\n{info}")
        c.execute("INSERT OR REPLACE INTO items (name, path, last_modified, item_type, info) VALUES (?, ?, ?, ?, ?)", 
                  (name, path, last_modified, item_type, info))
        conn.commit()

def close():
    global conn
    conn.close()