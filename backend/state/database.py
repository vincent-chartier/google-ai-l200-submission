"""Persistent SQLite database manager for session state, turns, and user memory.

Supports both non-blocking asynchronous operations via asyncio.to_thread and synchronous
methods for initializations and synchronous testing.
"""

import json
import sqlite3
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.config import DATABASE_PATH


class DatabaseManager:
    """Manages persistent SQLite storage for multi-agent sessions, conversation history, and preferences."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DATABASE_PATH
        if self.db_path != ":memory:" and not self.db_path.startswith("file:"):
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db_sync()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path.startswith("file:"):
            conn = sqlite3.connect(self.db_path, uri=True, check_same_thread=False)
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db_sync(self) -> None:
        """Creates required database tables synchronously on initialization."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_name TEXT DEFAULT 'Alex Morgan',
                    user_location TEXT DEFAULT 'Downtown',
                    conversation_summary TEXT DEFAULT '',
                    active_booking TEXT,
                    active_reservation TEXT,
                    last_recommended_movies TEXT,
                    compaction_metadata TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            # Migration check for user_name column if table existed
            cursor.execute("PRAGMA table_info(sessions)")
            existing_cols = [r[1] for r in cursor.fetchall()]
            if "user_name" not in existing_cols:
                cursor.execute("ALTER TABLE sessions ADD COLUMN user_name TEXT DEFAULT 'Alex Morgan'")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    text TEXT NOT NULL,
                    ui_summary TEXT,
                    timestamp REAL NOT NULL,
                    is_compacted INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    genre TEXT DEFAULT 'Sci-Fi',
                    rating REAL DEFAULT 5.0,
                    director TEXT,
                    created_at REAL NOT NULL,
                    UNIQUE(session_id, title),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_seen_movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    cinema TEXT DEFAULT 'Metropolis Cinema IMAX',
                    user_score REAL DEFAULT 5.0,
                    watched_date TEXT DEFAULT '2026-09-10',
                    created_at REAL NOT NULL,
                    UNIQUE(session_id, title),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    token TEXT PRIMARY KEY,
                    showtime_id TEXT NOT NULL,
                    movie_title TEXT NOT NULL,
                    cinema TEXT NOT NULL,
                    hall TEXT NOT NULL,
                    date_time TEXT NOT NULL,
                    seats TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    booking_fee REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    user_id TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS confirmed_bookings (
                    booking_id TEXT PRIMARY KEY,
                    showtime_id TEXT NOT NULL,
                    movie_title TEXT NOT NULL,
                    cinema TEXT NOT NULL,
                    hall TEXT NOT NULL,
                    date_time TEXT NOT NULL,
                    seats TEXT NOT NULL,
                    number_of_tickets INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    qr_code_token TEXT NOT NULL,
                    transaction_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS occupied_seats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    showtime_id TEXT NOT NULL,
                    seat_code TEXT NOT NULL,
                    booking_id TEXT,
                    UNIQUE(showtime_id, seat_code)
                )
            """)
            conn.commit()

    def load_session_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Synchronously loads a full session state dictionary from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                return None

            cursor.execute(
                "SELECT role, sender, text, ui_summary, timestamp FROM conversation_turns "
                "WHERE session_id = ? AND is_compacted = 0 ORDER BY id ASC",
                (session_id,)
            )
            turns = [
                {
                    "role": r["role"],
                    "sender": r["sender"],
                    "text": r["text"],
                    "ui_summary": r["ui_summary"],
                    "timestamp": r["timestamp"]
                }
                for r in cursor.fetchall()
            ]

            cursor.execute(
                "SELECT title, genre, rating, director FROM user_favorites WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            favorites = [
                {k: r[k] for k in ["title", "genre", "rating", "director"] if r[k] is not None}
                for r in cursor.fetchall()
            ]

            cursor.execute(
                "SELECT title, cinema, user_score, watched_date FROM user_seen_movies WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            seen = [
                {
                    "title": r["title"],
                    "cinema": r["cinema"],
                    "user_score": r["user_score"],
                    "watched_date": r["watched_date"]
                }
                for r in cursor.fetchall()
            ]

            user_name = session_row["user_name"] if "user_name" in session_row.keys() and session_row["user_name"] else "Alex Morgan"
            return {
                "user_id": session_row["user_id"],
                "user_name": user_name,
                "user_location": session_row["user_location"],
                "conversation_summary": session_row["conversation_summary"] or "",
                "active_booking": json.loads(session_row["active_booking"]) if session_row["active_booking"] else None,
                "active_reservation": json.loads(session_row["active_reservation"]) if session_row["active_reservation"] else None,
                "last_recommended_movies": json.loads(session_row["last_recommended_movies"]) if session_row["last_recommended_movies"] else [],
                "compaction_metadata": json.loads(session_row["compaction_metadata"]) if session_row["compaction_metadata"] else {},
                "conversation_history": turns,
                "favorite_movies": favorites,
                "seen_movies": seen
            }

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Asynchronously loads a full session state dictionary from SQLite."""
        return await asyncio.to_thread(self.load_session_sync, session_id)

    def save_session_sync(self, session_id: str, state: Dict[str, Any]) -> None:
        """Synchronously writes session state, favorites, and seen list to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, user_id, user_name, user_location, conversation_summary,
                    active_booking, active_reservation, last_recommended_movies,
                    compaction_metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_name = excluded.user_name,
                    user_location = excluded.user_location,
                    conversation_summary = excluded.conversation_summary,
                    active_booking = excluded.active_booking,
                    active_reservation = excluded.active_reservation,
                    last_recommended_movies = excluded.last_recommended_movies,
                    compaction_metadata = excluded.compaction_metadata,
                    updated_at = excluded.updated_at
            """, (
                session_id,
                state.get("user_id", session_id),
                state.get("user_name", "Alex Morgan"),
                state.get("user_location", "Downtown"),
                state.get("conversation_summary", ""),
                json.dumps(state.get("active_booking")) if state.get("active_booking") is not None else None,
                json.dumps(state.get("active_reservation")) if state.get("active_reservation") is not None else None,
                json.dumps(state.get("last_recommended_movies", [])),
                json.dumps(state.get("compaction_metadata", {})),
                now,
                now
            ))

            for fav in state.get("favorite_movies", []):
                cursor.execute("""
                    INSERT INTO user_favorites (session_id, title, genre, rating, director, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, title) DO UPDATE SET
                        genre = excluded.genre,
                        rating = excluded.rating,
                        director = excluded.director
                """, (
                    session_id,
                    fav.get("title", ""),
                    fav.get("genre", "Sci-Fi"),
                    fav.get("rating", 5.0),
                    fav.get("director"),
                    now
                ))

            for seen in state.get("seen_movies", []):
                cursor.execute("""
                    INSERT INTO user_seen_movies (session_id, title, cinema, user_score, watched_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id, title) DO UPDATE SET
                        cinema = excluded.cinema,
                        user_score = excluded.user_score,
                        watched_date = excluded.watched_date
                """, (
                    session_id,
                    seen.get("title", ""),
                    seen.get("cinema", "Metropolis Cinema IMAX"),
                    seen.get("user_score", 5.0),
                    seen.get("watched_date", "2026-09-10"),
                    now
                ))

            conn.commit()

    async def save_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """Asynchronously writes session state, favorites, and seen list to SQLite."""
        await asyncio.to_thread(self.save_session_sync, session_id, state)

    def append_turn_sync(self, session_id: str, turn: Dict[str, Any]) -> int:
        """Synchronously appends a conversation turn to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversation_turns (
                    session_id, role, sender, text, ui_summary, timestamp, is_compacted
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (
                session_id,
                turn.get("role", "user"),
                turn.get("sender", "user"),
                turn.get("text", ""),
                turn.get("ui_summary"),
                turn.get("timestamp", time.time())
            ))
            conn.commit()
            return cursor.lastrowid or 0

    async def append_turn(self, session_id: str, turn: Dict[str, Any]) -> int:
        """Asynchronously appends a conversation turn to SQLite."""
        return await asyncio.to_thread(self.append_turn_sync, session_id, turn)

    def mark_turns_compacted_sync(self, session_id: str, count: int) -> None:
        """Synchronously marks the oldest `count` uncompacted turns in SQLite as compacted."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE conversation_turns
                SET is_compacted = 1
                WHERE id IN (
                    SELECT id FROM conversation_turns
                    WHERE session_id = ? AND is_compacted = 0
                    ORDER BY id ASC
                    LIMIT ?
                )
            """, (session_id, count))
            conn.commit()

    async def mark_turns_compacted(self, session_id: str, count: int) -> None:
        """Asynchronously marks the oldest `count` uncompacted turns in SQLite as compacted."""
        await asyncio.to_thread(self.mark_turns_compacted_sync, session_id, count)

    def update_summary_and_metadata_sync(
        self,
        session_id: str,
        summary: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Synchronously updates rolling conversation summary and compaction metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions
                SET conversation_summary = ?,
                    compaction_metadata = ?,
                    updated_at = ?
                WHERE session_id = ?
            """, (
                summary,
                json.dumps(metadata),
                time.time(),
                session_id
            ))
            conn.commit()

    async def update_summary_and_metadata(
        self,
        session_id: str,
        summary: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Asynchronously updates rolling conversation summary and compaction metadata."""
        await asyncio.to_thread(self.update_summary_and_metadata_sync, session_id, summary, metadata)

    # ---------------------------------------------------------
    # Seat Reservations & Booking Transactions Persistence
    # ---------------------------------------------------------

    def save_reservation_sync(self, res: Dict[str, Any]) -> None:
        """Persists a temporary seat reservation hold to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reservations (
                    token, showtime_id, movie_title, cinema, hall, date_time,
                    seats, subtotal, booking_fee, total_amount, user_id, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                    seats = excluded.seats,
                    total_amount = excluded.total_amount,
                    expires_at = excluded.expires_at
            """, (
                res["token"],
                res["showtime_id"],
                res["movie_title"],
                res["cinema"],
                res["hall"],
                res["date_time"],
                json.dumps(res.get("seats", [])),
                res.get("subtotal", 0.0),
                res.get("booking_fee", 0.0),
                res.get("total_amount", 0.0),
                res.get("user_id", "guest_user"),
                res.get("expires_at", time.time() + 600),
                time.time()
            ))
            conn.commit()

    async def save_reservation(self, res: Dict[str, Any]) -> None:
        """Asynchronously persists a temporary seat reservation hold to SQLite."""
        await asyncio.to_thread(self.save_reservation_sync, res)

    def get_reservation_sync(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieves a reservation hold by token from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reservations WHERE token = ?", (token,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "token": row["token"],
                "showtime_id": row["showtime_id"],
                "movie_title": row["movie_title"],
                "cinema": row["cinema"],
                "hall": row["hall"],
                "date_time": row["date_time"],
                "seats": json.loads(row["seats"]) if row["seats"] else [],
                "subtotal": row["subtotal"],
                "booking_fee": row["booking_fee"],
                "total_amount": row["total_amount"],
                "user_id": row["user_id"],
                "expires_at": row["expires_at"]
            }

    async def get_reservation(self, token: str) -> Optional[Dict[str, Any]]:
        """Asynchronously retrieves a reservation hold by token from SQLite."""
        return await asyncio.to_thread(self.get_reservation_sync, token)

    def delete_reservation_sync(self, token: str) -> None:
        """Deletes an expired or fulfilled reservation hold from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reservations WHERE token = ?", (token,))
            conn.commit()

    async def delete_reservation(self, token: str) -> None:
        """Asynchronously deletes an expired or fulfilled reservation hold from SQLite."""
        await asyncio.to_thread(self.delete_reservation_sync, token)

    def save_booking_sync(self, booking: Dict[str, Any]) -> None:
        """Persists a confirmed ticket booking record to SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO confirmed_bookings (
                    booking_id, showtime_id, movie_title, cinema, hall, date_time,
                    seats, number_of_tickets, total_amount, payment_method, user_name,
                    qr_code_token, transaction_timestamp, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(booking_id) DO UPDATE SET
                    status = excluded.status
            """, (
                booking["booking_id"],
                booking.get("showtime_id", "SH-DUNE-1930"),
                booking["movie_title"],
                booking["cinema"],
                booking["hall"],
                booking["date_time"],
                json.dumps(booking.get("seats", [])),
                booking.get("number_of_tickets", len(booking.get("seats", []))),
                booking.get("total_amount", 0.0),
                booking.get("payment_method", "Google Pay"),
                booking.get("user_name", "Alex Morgan"),
                booking.get("qr_code_token", ""),
                booking.get("transaction_timestamp", ""),
                booking.get("status", "CONFIRMED"),
                time.time()
            ))
            conn.commit()

    async def save_booking(self, booking: Dict[str, Any]) -> None:
        """Asynchronously persists a confirmed ticket booking record to SQLite."""
        await asyncio.to_thread(self.save_booking_sync, booking)

    def get_booking_sync(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a confirmed booking record from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM confirmed_bookings WHERE booking_id = ?", (booking_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "booking_id": row["booking_id"],
                "showtime_id": row["showtime_id"],
                "movie_title": row["movie_title"],
                "cinema": row["cinema"],
                "hall": row["hall"],
                "date_time": row["date_time"],
                "seats": json.loads(row["seats"]) if row["seats"] else [],
                "number_of_tickets": row["number_of_tickets"],
                "total_amount": row["total_amount"],
                "payment_method": row["payment_method"],
                "user_name": row["user_name"],
                "qr_code_token": row["qr_code_token"],
                "transaction_timestamp": row["transaction_timestamp"],
                "status": row["status"]
            }

    async def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        """Asynchronously retrieves a confirmed booking record from SQLite."""
        return await asyncio.to_thread(self.get_booking_sync, booking_id)

    def update_booking_status_sync(self, booking_id: str, status: str) -> None:
        """Updates the status of a booking in SQLite (e.g. CANCELLED)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE confirmed_bookings SET status = ? WHERE booking_id = ?", (status, booking_id))
            conn.commit()

    async def update_booking_status(self, booking_id: str, status: str) -> None:
        """Asynchronously updates the status of a booking in SQLite."""
        await asyncio.to_thread(self.update_booking_status_sync, booking_id, status)

    def get_occupied_seats_sync(self, showtime_id: str) -> List[str]:
        """Fetches all permanently occupied seats for a showtime from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT seat_code FROM occupied_seats WHERE showtime_id = ?", (showtime_id,))
            return [r["seat_code"] for r in cursor.fetchall()]

    async def get_occupied_seats(self, showtime_id: str) -> List[str]:
        """Asynchronously fetches all permanently occupied seats for a showtime from SQLite."""
        return await asyncio.to_thread(self.get_occupied_seats_sync, showtime_id)

    def add_occupied_seats_sync(
        self,
        showtime_id: str,
        seats: List[str],
        booking_id: Optional[str] = None
    ) -> None:
        """Records newly occupied seats for a showtime in SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for s in seats:
                cursor.execute("""
                    INSERT INTO occupied_seats (showtime_id, seat_code, booking_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(showtime_id, seat_code) DO NOTHING
                """, (showtime_id, s, booking_id))
            conn.commit()

    async def add_occupied_seats(
        self,
        showtime_id: str,
        seats: List[str],
        booking_id: Optional[str] = None
    ) -> None:
        """Asynchronously records newly occupied seats for a showtime in SQLite."""
        await asyncio.to_thread(self.add_occupied_seats_sync, showtime_id, seats, booking_id)

    def remove_occupied_seats_sync(self, showtime_id: str, seats: List[str]) -> None:
        """Removes occupied seats for a cancelled booking from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for s in seats:
                cursor.execute(
                    "DELETE FROM occupied_seats WHERE showtime_id = ? AND seat_code = ?",
                    (showtime_id, s)
                )
            conn.commit()

    async def remove_occupied_seats(self, showtime_id: str, seats: List[str]) -> None:
        """Asynchronously removes occupied seats for a cancelled booking from SQLite."""
        await asyncio.to_thread(self.remove_occupied_seats_sync, showtime_id, seats)

