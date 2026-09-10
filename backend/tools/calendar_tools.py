"""Calendar tools for cinema outings invite dispatch."""

import urllib.parse
from datetime import datetime, timedelta

def create_calendar_invite(
    movie_title: str,
    cinema: str,
    date_time_str: str,
    duration_minutes: int = 150,
    seats: list[str] = None
) -> dict:
    """Creates a calendar event payload and .ics invite for a cinema outing.
    
    Args:
        movie_title: Title of the movie.
        cinema: Cinema name and hall.
        date_time_str: Date and time formatted as 'YYYY-MM-DD HH:MM'.
        duration_minutes: Estimated runtime plus trailers (default: 150 mins).
        seats: List of booked seats (e.g. ['F7', 'F8']).
        
    Returns:
        Dictionary with event details, .ics formatted string, and web calendar links.
    """
    try:
        start_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        # Fallback to tomorrow 19:30 if date string format differs
        start_dt = datetime.utcnow() + timedelta(days=1)
        start_dt = start_dt.replace(hour=19, minute=30, second=0, microsecond=0)
        
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    
    seat_info = f"Seats: {', '.join(seats)}" if seats else "General Admission"
    summary = f"🎬 Cinema Outing: {movie_title}"
    description = f"Enjoying '{movie_title}' at {cinema}.\n{seat_info}\nEnjoy the show!"
    location = cinema
    
    from datetime import timezone
    # Formats for iCal: YYYYMMDDTHHMMSSZ
    dt_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dt_start = start_dt.strftime("%Y%m%dT%H%M%SZ")
    dt_end = end_dt.strftime("%Y%m%dT%H%M%SZ")
    uid = f"cinema-{start_dt.strftime('%Y%m%d%H%M')}-{urllib.parse.quote_plus(movie_title)}@cinemaoutings.app"
    
    ics_content = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Cinema Outings AI//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:REQUEST\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{dt_stamp}\r\n"
        f"DTSTART:{dt_start}\r\n"
        f"DTEND:{dt_end}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    
    # Google Calendar Web URL generator
    gcal_params = {
        "action": "TEMPLATE",
        "text": summary,
        "dates": f"{dt_start}/{dt_end}",
        "details": description,
        "location": location
    }
    gcal_url = "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(gcal_params)
    
    return {
        "success": True,
        "event_title": summary,
        "movie_title": movie_title,
        "cinema": cinema,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "seats": seats or [],
        "ics_content": ics_content,
        "google_calendar_url": gcal_url
    }
