import json
import sqlite3

# Load JSON
with open('seed_posts.json', 'r') as f:
    posts = json.load(f)

# Connect to the database
conn = sqlite3.connect('posts.db')
cur = conn.cursor()

# Insert data
for post in posts:
    cur.execute(
        "INSERT INTO posts (text, label) VALUES (?, ?)",
        (post["text"], post.get("label", None))
    )

conn.commit()
conn.close()
print(f"Imported {len(posts)} posts.")
