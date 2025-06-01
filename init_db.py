import sqlite3

with open('schema.sql') as f:
    schema = f.read()

conn = sqlite3.connect('posts.db')
conn.executescript(schema)
conn.commit()
conn.close()

print("Database initialized.")
