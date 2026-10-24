import json
import re
import sqlite3
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "smashpro.sqlite3"
PORT = 8000
MAX_REQUEST_BYTES = 10_000
ALLOWED_GAMES = {"pickleball", "paddleball"}
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


def initialize_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                game TEXT NOT NULL CHECK (game IN ('pickleball', 'paddleball')),
                booking_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                duration_hours INTEGER NOT NULL DEFAULT 1 CHECK (duration_hours = 1),
                price_inr INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def booking_price(game, booking_day):
    if game == "paddleball":
        return 2000
    return 600 if booking_day.weekday() >= 5 else 400


class SmashProHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.startswith("/api/"):
            self.send_error(404, "API endpoint not found.")
            return
        static_file = STATIC_FILES.get(path)
        if static_file is None:
            self.send_error(404, "File not found.")
            return
        filename, content_type = static_file
        body = (BASE_DIR / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/bookings":
            self.send_json(404, {"error": "API endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid booking request."})
            return
        if content_length < 1 or content_length > MAX_REQUEST_BYTES:
            self.send_json(413, {"error": "Booking request is empty or too large."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "Please submit a valid booking request."})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "Please submit a valid booking request."})
            return

        name = payload.get("name")
        phone = payload.get("phone")
        game = payload.get("game")
        date_value = payload.get("date")
        time_value = payload.get("time")
        if not all(isinstance(value, str) for value in (name, phone, game, date_value, time_value)):
            self.send_json(400, {"error": "Please complete all booking fields."})
            return

        name = name.strip()
        phone = phone.strip()
        if not name or len(name) > 80:
            self.send_json(400, {"error": "Enter a name of up to 80 characters."})
            return
        if not re.fullmatch(r"\+?[0-9][0-9\s()-]{8,18}", phone) or len(re.sub(r"\D", "", phone)) not in range(9, 16):
            self.send_json(400, {"error": "Enter a valid phone number."})
            return
        if game not in ALLOWED_GAMES:
            self.send_json(400, {"error": "Choose a valid game."})
            return
        try:
            booking_day = date.fromisoformat(date_value)
        except ValueError:
            self.send_json(400, {"error": "Choose a valid booking date."})
            return
        if booking_day < date.today():
            self.send_json(400, {"error": "Booking dates must be today or later."})
            return
        if not re.fullmatch(r"(?:0[6-9]|1[0-9]|2[0-2]):00", time_value):
            self.send_json(400, {"error": "Choose a start time between 6:00 AM and 10:00 PM."})
            return

        price = booking_price(game, booking_day)
        with sqlite3.connect(DATABASE) as connection:
            connection.execute(
                """
                INSERT INTO bookings
                    (name, phone, game, booking_date, start_time, price_inr, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    phone,
                    game,
                    date_value,
                    time_value,
                    price,
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )

        self.send_json(201, {"saved": True, "priceInr": price})

    def log_message(self, format_string, *args):
        print(f"{self.log_date_time_string()} {self.address_string()} {format_string % args}")


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), SmashProHandler)
    print(f"SmashPro is running at http://127.0.0.1:{PORT}")
    print(f"SQLite database: {DATABASE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down SmashPro.")
    finally:
        server.server_close()
