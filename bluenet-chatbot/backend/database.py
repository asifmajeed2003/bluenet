import sqlite3

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('knowledge_base.db')
        print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn):
    try:
        sql_articles = """
        CREATE TABLE IF NOT EXISTS articles (
            id integer PRIMARY KEY,
            title text NOT NULL,
            content text NOT NULL,
            language text NOT NULL
        );
        """
        sql_users = """
        CREATE TABLE IF NOT EXISTS users (
            id integer PRIMARY KEY,
            fisher_id text UNIQUE,
            language text,
            location text
        );
        """
        conn.execute(sql_articles)
        conn.execute(sql_users)
    except sqlite3.Error as e:
        print(e)

if __name__ == '__main__':
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        conn.close()
    else:
        print("Error! cannot create the database connection.")
