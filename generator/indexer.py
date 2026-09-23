import os
import sqlite3


class SQLiteIndexer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if os.path.exists(db_path):
            os.remove(db_path)

        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode = OFF")
        self.conn.execute("PRAGMA synchronous = 0")
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE threads (
                    thread_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    discriminator TEXT,
                    created_at TEXT,
                    closed_at TEXT,
                    message_count INTEGER,
                    path TEXT NOT NULL
                )
            """)
            self.conn.execute("CREATE INDEX idx_user_id ON threads(user_id)")
            self.conn.execute("CREATE INDEX idx_created_at ON threads(created_at)")

    def insert_batch(self, rows: list):
        with self.conn:
            self.conn.executemany(
                "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows
            )

    def close(self):
        # Optimize and clean before distribution
        self.conn.execute("VACUUM")
        self.conn.close()
