import sqlite3, os
conn = sqlite3.connect(os.path.expanduser('~/.n8n/database.sqlite'))
columns = [x[1] for x in conn.execute('PRAGMA table_info(user_api_keys)')]
data = conn.execute('SELECT * FROM user_api_keys').fetchall()
print(columns)
print(data)
