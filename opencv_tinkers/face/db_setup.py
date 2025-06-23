import sqlite3

db_conn = sqlite3.connect("face.db")
c = db_conn.cursor() # this one represents a temporary pointer to the database -- Cursor type

# so we need 2 tables .. one for users and one for attendance

# creating the user table
c.execute('''
          CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          encoding BLOB NOT NULL
          )
          ''')

# creating the attendance table
c.execute('''
          CREATE TABLE IF NOT EXISTS attendance (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          timestamp TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id)
          )
          ''')

db_conn.commit() # maybe something like commit the changes after changing the data
db_conn.close() # resource closing
