# SmashPro Pickleball Arena

A responsive landing page and WhatsApp booking handoff for SmashPro. The frontend uses plain HTML, CSS, and JavaScript. The Python standard-library backend saves booking requests to SQLite before opening WhatsApp; no package installation is required.

## Run locally

From this folder, run:

```powershell
python server.py
```

Then open <http://127.0.0.1:8000>. The database file `smashpro.sqlite3` is created automatically when the server starts.

## Booking rules

- Arena hours: every day, 6:00 AM–11:00 PM. One-hour start times are available from 6:00 AM through 10:00 PM.
- Pickleball: ₹400/hour Monday–Friday; ₹600/hour Saturday–Sunday.
- Paddleball: ₹2,000/hour every day.
- A paddle and ball are included with either game.
- The booking form saves each request to SQLite, then opens WhatsApp addressed to +91 96038 13946 with the details prefilled. The customer must tap **Send** in WhatsApp to deliver it.
- The website does not display a booking confirmation containing the submitted details.

To view saved booking requests on the server computer, run this in PowerShell from the project folder:

```powershell
@'
import sqlite3
connection = sqlite3.connect("smashpro.sqlite3")
for booking in connection.execute(
    "SELECT name, phone, game, booking_date, start_time, price_inr FROM bookings ORDER BY id DESC"
):
    print(booking)
'@ | python -
```

The Google Maps embed and directions link search for “SmashPro Pickleball Arena.” Add the arena's exact address or coordinates to `index.html` if you want the map to point to a specific location.
