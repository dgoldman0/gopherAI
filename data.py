from lark import Lark, Transformer, v_args, Tree
import sqlite3
import re
from datetime import datetime

conn = None

# Define the grammar
grammar = """
    start: or_test
    or_test: and_test ("OR" and_test)*
    and_test: not_test ("AND" not_test)*
    not_test: "NOT" not_test | comparison
    comparison: column ("=" | "!=" | ">" | ">=" | "<" | "<=" | "LIKE") value
    column: "name" | "path" | "last_modified" | "item_type" | "info"
    value: ESCAPED_STRING | SIGNED_INT | DATETIME
    DATETIME: /\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/
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
                datetime.strptime(datetime_value, '%Y-%m-%d %H:%M:%S')  # Check if the datetime string matches the format
                return datetime_value
            except ValueError:
                raise ValueError(f"Invalid datetime format: {datetime_value}, expected format: YYYY-MM-DD HH:MM:SS")
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
            'item_type': 'INTEGER',
            'info': 'TEXT'
        }
        return column_types[column]

    def is_valid_type(self, column_type, value):
        if column_type == 'TEXT' and isinstance(value, str):
            return True
        elif column_type == 'INTEGER' and isinstance(value, int):
            return True
        elif column_type == 'DATETIME' and re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):  # Check if value matches datetime pattern
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

class DatabaseSearcher:
    def __init__(self, conn):
        self.conn = conn

    def search(self, query):
        # Parse the query
        sql_where_clause = parser.parse(query)

        # Prepare the SQL query
        sql_query = f"""
            SELECT *
            FROM items
            WHERE {sql_where_clause}
        """

        # Execute the query and fetch the results
        cursor = self.conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        return rows
    
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