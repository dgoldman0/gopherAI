from lark import Lark, Transformer, v_args, Tree
import sqlite3
import re
from datetime import datetime, timedelta
from urllib.parse import quote
import time
import secrets

from lark import Lark, Transformer, v_args, Tree
import sqlite3
import re
from datetime import datetime
from eth_account import Account

# I want to add more data that could be useful for search, such as some kind of extra tag system. Searches should be rich.

# Define the grammar
grammar = """
    start: or_test
    or_test: and_test ("OR" and_test)*
    and_test: not_test ("AND" not_test)*
    not_test: "NOT" not_test | comparison
    comparison: column ("=" | "!=" | ">" | ">=" | "<" | "<=" | "LIKE") value
    column: "name" | "path" | "last_modified" | "item_type" | "short_description" | "description"
    value: ESCAPED_STRING | SIGNED_INT | DATETIME
    DATETIME: /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/
    %import common.ESCAPED_STRING
    %import common.SIGNED_INT
    %import common.WS
    %ignore WS
"""

# Define the transformer
@v_args(inline=True)
class QueryTransformer(Transformer):
    def column(self, name):
        return name[0]

    def value(self, value):
        value = value[0]
        if isinstance(value, Tree) and value.data == 'SIGNED_INT':
            return int(value.children[0])
        elif isinstance(value, Tree) and value.data == 'ESCAPED_STRING':
            return re.sub(r'\W+', '', value.children[0][1:-1])  # Remove quotes and sanitize string
        elif isinstance(value, Tree) and value.data == 'DATETIME':
            # Validate datetime format
            datetime_value = value.children[0]
            try:
                datetime.strptime(datetime_value, '%Y-%m-%dT%H:%M:%SZ')  # Check if the datetime string matches the format
                return datetime_value
            except ValueError:
                raise ValueError(f"Invalid datetime format: {datetime_value}, expected format: YYYY-MM-DDTHH:MM:SSZ")
        else:
            return value

    def comparison(self, items):
        column, operator, value = items
        column_type = self.get_column_type(column)
        if not self.is_valid_type(column_type, value):
            raise ValueError(f"Invalid value '{value}' for column '{column}' of type '{column_type}'")
        return f"{column} {operator} '{value}'"

    def get_column_type(self, column):
        column_types = {
            'name': 'TEXT',
            'path': 'TEXT',
            'last_modified': 'DATETIME',
            'item_type': 'TEXT',
            'short_description': 'TEXT',
            'description': 'TEXT'
        }
        return column_types[column]

    def is_valid_type(self, column_type, value):
        if column_type == 'TEXT' and isinstance(value, str):
            return True
        elif column_type == 'INTEGER' and isinstance(value, int):
            return True
        elif column_type == 'DATETIME' and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):  # Check if value matches datetime pattern
            return True
        else:
            return False

    def not_test(self, items):
        if len(items) == 1:
            return items[0]
        else:
            return f"NOT {items[1]}"

    def and_test(self, items):
        return f" AND ".join(items)

    def or_test(self, items):
        return f" OR ".join(items)

    def start(self, items):
        return items[0]

# Create the parser
parser = Lark(grammar, parser='lalr', transformer=QueryTransformer())

# Things like server URL and port should be in here as well.
class DataManager:
    conn = None
    def __init__(self, db):
        # Initialize the database.
        print("Initializing database...")
        self.conn = sqlite3.connect(db)  # You can replace 'my_database.db' with your preferred database name.
        c = self.conn.cursor()
        c.execute('''
                CREATE TABLE IF NOT EXISTS items
                (name TEXT, path TEXT, last_modified TEXT, item_type TEXT, short_description TEXT, description TEXT, mime_type TEXT, size INTEGER,
                PRIMARY KEY(name, path))
                ''')
        # Maybe rather than sessions it can be "access control"
        c.execute('''
                CREATE TABLE IF NOT EXISTS access
                (access_id TEXT, address TEXT, message TEXT, created datetime)
                ''')
        c.execute('''
                CREATE TABLE IF NOT EXISTS settings
                (host TEXT, port INTEGER, PRIMARY KEY(host, port))
                ''')
        # If there isn't any settings info yet, add it with host as localhost and port as 10070
        c.execute("INSERT INTO settings (host, port) SELECT 'localhost', 10070 WHERE NOT EXISTS(SELECT 1 FROM settings)")
        self.conn.commit()

    def host_port(self):
        # Returns host and port from the settings table
        c = self.conn.cursor()
        c.execute("SELECT host, port FROM settings LIMIT 1")
        data = c.fetchone()
        if data is not None:
            return data
        else:
            return None
        
    def is_valid_accessid(self, id, signed_message):
        c = self.conn.cursor()
        
        # Fetch the associated row using the provided id.
        c.execute("SELECT address, message FROM access WHERE access_id = ?", (id,))
        row = c.fetchone()
        
        # If the row doesn't exist, return False.
        if not row:
            return False

        address, original_message = row

        # Verify the signed_message using the Ethereum address.
        try:
            recovered_address = Account.recover_message(original_message, signature=signed_message)
            if recovered_address.lower() == address.lower():
                return True
        except:
            pass

        return False

    def accessid_exists(self, id):
        c = self.conn.cursor()
        
        # Check the count of rows with the provided id.
        c.execute("SELECT COUNT(1) FROM access WHERE access_id = ?", (id,))
        count = c.fetchone()[0]
        
        return count > 0
 
    def add_accessid(self, id, address):
        # Generate a unique message. 
        message = f"{secrets.token_hex(16)}-{time.time()}"
        # Add the information to the database
        c = self.conn.cursor()
        c.execute("INSERT INTO access (access_id, address, message, created) VALUES (?, ?, ?, datetime('now'))", (id, address, message))
        self.conn.commit()
        return message
    
    def revoke_accessid(self, id):
        with self.conn:
            self.conn.execute("DELETE FROM access WHERE access_id = ?", (id))

    def search(self, query):
        # Parse the query
        sql_where_clause = parser.parse(query)

        # Prepare the SQL query
        sql_query = f"""
            item_type, short_description, description, mime_type, size, last_modified
            FROM items
            WHERE {sql_where_clause}
        """

        # Execute the query and fetch the results
        cursor = self.conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        # Revise to send as a string in Gopher menu format.
        host, port = self.host_port()
        # item_line = f"{result[0]}{quote(result[1])}\t{path}\t{host}\t{port}\t+Description:{quote(result[2])}\t+MIME:{result[3]}\t+Size:{result[4]}\t+Modified:{result[5]}"

        return rows
    
    # Return None if no entry found.
    def last_modified(self, name, path):
        c = self.conn.cursor()
        c.execute("SELECT last_modified FROM items WHERE name=? AND path=?", (name, path))
        result = c.fetchone()
        if result is None:
            return None
        else:
            return result[0]

    # Get the item info or None associated with name and path, if last_modified is None, else set the entry.
    def item_info(self, name, path, last_modified=None, item_type=None, short_description=None, description=None, mime_type=None, size=None):
        c = self.conn.cursor()

        if last_modified is None:
            c.execute("SELECT item_type, short_description, description, mime_type, size, last_modified FROM items WHERE name=? AND path=?", (name, path))
            result = c.fetchone()
            if result is None:
                return None
            else:
                host, port = self.host_port()
                item_line = f"{result[0]}{quote(result[1])}\t{path}\t{host}\t{port}\t+DESCRIPTION:{quote(result[2])}\t+MIME:{result[3]}\t+SIZE:{result[4]}\t+MODIFIED:{result[5]}"
                return result[0], item_line
        else:
            c.execute("INSERT OR REPLACE INTO items (name, path, last_modified, item_type, short_description, description, mime_type, size) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                    (name, path, last_modified, item_type, short_description, description, mime_type, size))
        self.conn.commit()

    def close(self):
        self.conn.close()