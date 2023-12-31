from flask import redirect, url_for
from .. import app
import sqlite3

DATABASE = 'database.db'

@app.route('/setup')
def setup():
    con = sqlite3.connect(DATABASE)
    # con.execute("CREATE TABLE IF NOT EXISTS books (title, price, arrival_day)")
    # ChatGPT chat history
    con.execute("CREATE TABLE IF NOT EXISTS chat_history (seq INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT)")
    con.close()

    return redirect(url_for('index'))