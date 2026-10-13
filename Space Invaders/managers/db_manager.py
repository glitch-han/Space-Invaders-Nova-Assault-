import json
import os
import mysql.connector
from mysql.connector import Error


class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings_path="settings.json"):
        if self._initialized:
            return
        self._initialized = True

        self.settings_path = settings_path
        self.config = self._load_config()
        self.connection = None
        self.is_connected = False

        self.connect()

    def _load_config(self):
        default_config = {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "space_invaders_cordero_db",
        }
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                    default_config.update(settings.get("database", {}))
        except (json.JSONDecodeError, OSError) as e:
            print(f"[DB] Could not read {self.settings_path}, using defaults. ({e})")
        return default_config

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
            )
            self.is_connected = True
            print("[DB] Connected to MySQL successfully.")
        except Error as e:
            self.is_connected = False
            print(f"[DB] Connection failed: {e}")

    def _ensure_connection(self):
        if self.connection is None or not self.connection.is_connected():
            self.connect()
        return self.is_connected

    def register_player(self, username):
        if not self._ensure_connection():
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO players (username) VALUES (%s)", (username,)
            )
            self.connection.commit()
            new_id = cursor.lastrowid
            cursor.close()
            return new_id
        except Error as e:
            print(f"[DB] register_player failed: {e}")
            return None

    def save_score(self, player_id, score, level=1):
        if not self._ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO scores (player_id, score, level) VALUES (%s, %s, %s)",
                (player_id, score, level),
            )
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"[DB] save_score failed: {e}")
            return False

    def find_player_by_username(self, username):
        if not self._ensure_connection():
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT player_id FROM players WHERE username = %s LIMIT 1",
                (username,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else None
        except Error as e:
            print(f"[DB] find_player_by_username failed: {e}")
            return None

    def get_or_create_player(self, username):
        existing_id = self.find_player_by_username(username)
        if existing_id is not None:
            return existing_id
        return self.register_player(username)

    def get_player_avatar(self, player_id):
        if not self._ensure_connection():
            return "white"
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT avatar_color FROM players WHERE player_id = %s", (player_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else "white"
        except Error:
            return "white"

    def get_player_ship(self, player_id):
        if not self._ensure_connection():
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT ship_model FROM players WHERE player_id = %s", (player_id,)
            )
            row = cursor.fetchone()
            cursor.close()
            return row[0] if row else None
        except Error:
            return None

    def get_leaderboard(self, limit=10):
        if not self._ensure_connection():
            return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT username, score AS high_score, level
                FROM (
                    SELECT p.username AS username,
                           s.score AS score,
                           s.level AS level,
                           ROW_NUMBER() OVER (
                               PARTITION BY s.player_id
                               ORDER BY s.score DESC, s.created_at ASC
                           ) AS rn
                    FROM scores s
                    JOIN players p ON p.player_id = s.player_id
                ) ranked
                WHERE rn = 1
                ORDER BY high_score DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except Error as e:
            print(f"[DB] get_leaderboard failed: {e}")
            return []

    def get_player_stats(self, player_id):
        if not self._ensure_connection():
            return {"games_played": 0, "high_score": 0, "avg_score": 0}
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT COUNT(*) AS games_played,
                       COALESCE(MAX(score), 0) AS high_score,
                       COALESCE(AVG(score), 0) AS avg_score
                FROM scores
                WHERE player_id = %s
                """,
                (player_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            return row
        except Error as e:
            print(f"[DB] get_player_stats failed: {e}")
            return {"games_played": 0, "high_score": 0, "avg_score": 0}

    def update_player_profile(self, player_id, new_username):
        if not self._ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE players SET username = %s WHERE player_id = %s",
                (new_username, player_id),
            )
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"[DB] update_player_profile failed: {e}")
            return False

    def update_player_avatar(self, player_id, color_name):
        if not self._ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE players SET avatar_color = %s WHERE player_id = %s",
                (color_name, player_id),
            )
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"[DB] update_player_avatar failed (migration run?): {e}")
            return False

    def update_player_ship(self, player_id, ship_model):
        if not self._ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE players SET ship_model = %s WHERE player_id = %s",
                (ship_model, player_id),
            )
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"[DB] update_player_ship failed (add_ship_model.sql run?): {e}")
            return False

    def delete_player(self, player_id):
        if not self._ensure_connection():
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM scores WHERE player_id = %s", (player_id,))
            cursor.execute("DELETE FROM players WHERE player_id = %s", (player_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"[DB] delete_player failed: {e}")
            return False

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.is_connected = False
