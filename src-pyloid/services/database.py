import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
from services.logger import debug


class DatabaseService:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            app_data = Path.home() / ".VoiceFlow"
            app_data.mkdir(exist_ok=True)
            db_path = app_data / "VoiceFlow.db"

        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # History table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                word_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    # Settings methods
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        conn.close()

    def get_all_settings(self) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        return {row["key"]: row["value"] for row in rows}

    # History methods
    def add_history(self, text: str) -> int:
        char_count = len(text)
        word_count = len(text.split())
        created_at = datetime.now().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO history (text, char_count, word_count, created_at)
               VALUES (?, ?, ?, ?)""",
            (text, char_count, word_count, created_at)
        )
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return history_id

    def get_history(self, limit: int = 100, offset: int = 0, search: str = None) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()

        if search:
            cursor.execute(
                """SELECT * FROM history
                   WHERE text LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (f"%{search}%", limit, offset)
            )
        else:
            cursor.execute(
                """SELECT * FROM history
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            )

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_history(self, history_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE id = ?", (history_id,))
        conn.commit()
        conn.close()

    def clear_old_history(self, days: int):
        """Clear history older than specified days. -1 means keep forever."""
        if days < 0:
            return

        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """Get aggregate stats from history."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get totals
        cursor.execute("""
            SELECT
                COUNT(*) as total_transcriptions,
                COALESCE(SUM(word_count), 0) as total_words,
                COALESCE(SUM(char_count), 0) as total_characters
            FROM history
        """)
        row = cursor.fetchone()

        # Calculate streak (consecutive days with transcriptions)
        cursor.execute("""
            SELECT DISTINCT DATE(created_at) as day
            FROM history
            ORDER BY day DESC
        """)
        days = [r["day"] for r in cursor.fetchall()]
        streak = self._calculate_streak(days)

        conn.close()
        result = {
            "totalTranscriptions": int(row["total_transcriptions"]),
            "totalWords": int(row["total_words"]),
            "totalCharacters": int(row["total_characters"]),
            "streakDays": streak,
        }
        debug(f"Database get_stats: {result}")
        return result

    def reset_all_data(self):
        """Delete all data and reset to fresh state."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Clear all history
        cursor.execute("DELETE FROM history")

        # Clear all settings (will use defaults on next load)
        cursor.execute("DELETE FROM settings")

        conn.commit()
        conn.close()
        debug("All data has been reset")

    def _calculate_streak(self, days: list) -> int:
        """Calculate consecutive days streak from list of date strings."""
        if not days:
            return 0

        from datetime import datetime, timedelta

        streak = 0
        today = datetime.now().date()

        for i, day_str in enumerate(days):
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
            expected = today - timedelta(days=i)

            # Allow for today or yesterday to start the streak
            if i == 0 and (day == today or day == today - timedelta(days=1)):
                streak = 1
                if day == today - timedelta(days=1):
                    expected = today - timedelta(days=1)
            elif day == expected:
                streak += 1
            else:
                break

        return streak
