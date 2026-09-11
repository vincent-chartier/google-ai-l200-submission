import uuid
import time
from datetime import datetime
from typing import Optional

from backend.state.database import DatabaseManager

# Singleton database instance for persistent transactions
_DB_INSTANCE: Optional[DatabaseManager] = None

def get_booking_db() -> DatabaseManager:
    """Returns persistent SQLite DatabaseManager instance."""
    global _DB_INSTANCE
    if _DB_INSTANCE is None:
        _DB_INSTANCE = DatabaseManager()
    return _DB_INSTANCE

# In-memory storage / cache for fast access
ACTIVE_RESERVATIONS = {}
CONFIRMED_BOOKINGS = {}

# Default occupied seats for realistic theater layout simulation
OCCUPIED_SEATS_MAP = {
    "SH-DUNE-1930": ["C3", "C4", "D4", "D5", "E4", "E5", "E6"],
    "SH-DUNE-1630": ["B4", "B5", "F3", "F4"],
    "SH-INT-1800": ["D3", "D4", "D5", "D6", "E3", "E4"],
    "SH-ALIEN-2030": ["A1", "A2", "C5", "C6"],
}

SHOWTIME_METADATA = {
    "SH-DUNE-1930": {
        "movie_title": "Dune: Part Two",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "IMAX Laser Hall",
        "date_time": "2026-09-12 19:30",
        "unit_price": 19.50
    },
    "SH-DUNE-1630": {
        "movie_title": "Dune: Part Two",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "IMAX Laser Hall",
        "date_time": "2026-09-12 16:30",
        "unit_price": 19.50
    },
    "SH-INT-1800": {
        "movie_title": "Interstellar",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "IMAX Laser Hall",
        "date_time": "2026-09-13 18:00",
        "unit_price": 22.00
    },
    "SH-ALIEN-2030": {
        "movie_title": "Alien: Romulus",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "Dolby Cinema Suite",
        "date_time": "2026-09-12 20:30",
        "unit_price": 17.00
    }
}


def get_seat_availability(showtime_id: str) -> dict:
    """Retrieves the real-time seating chart and availability for a movie showtime.
    
    Args:
        showtime_id: Unique identifier for the screening (e.g. 'SH-DUNE-1930').
        
    Returns:
        Dictionary containing rows, seats, availability status, and pricing.
    """
    meta = SHOWTIME_METADATA.get(showtime_id, {
        "movie_title": "Cinema Screening",
        "cinema": "Metropolis Cinema IMAX",
        "hall": "Main Hall",
        "date_time": "2026-09-12 19:30",
        "unit_price": 18.00
    })
    
    occupied = set(OCCUPIED_SEATS_MAP.get(showtime_id, ["C3", "C4", "D4"]))
    # Add seats from persistent SQLite database
    try:
        db_occupied = get_booking_db().get_occupied_seats_sync(showtime_id)
        occupied.update(db_occupied)
    except Exception:
        pass

    # Also include seats currently locked in active reservations
    for res in ACTIVE_RESERVATIONS.values():
        if res.get("showtime_id") == showtime_id and res.get("expires_at", 0) > time.time():
            occupied.update(res.get("seats", []))

    rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
    seats_per_row = 8
    
    seat_grid = []
    for r in rows:
        row_seats = []
        for col in range(1, seats_per_row + 1):
            seat_code = f"{r}{col}"
            tier = "VIP" if r in ["D", "E", "F"] and col in [3, 4, 5, 6] else "Standard"
            price = meta["unit_price"] + (2.50 if tier == "VIP" else 0.0)
            status = "occupied" if seat_code in occupied else "available"
            
            row_seats.append({
                "seat_id": seat_code,
                "row": r,
                "column": col,
                "tier": tier,
                "price": price,
                "status": status
            })
        seat_grid.append({"row": r, "seats": row_seats})
        
    return {
        "showtime_id": showtime_id,
        "movie_title": meta["movie_title"],
        "cinema": meta["cinema"],
        "hall": meta["hall"],
        "date_time": meta["date_time"],
        "base_price": meta["unit_price"],
        "seat_grid": seat_grid
    }


def hold_seats_reservation(showtime_id: str, seats: list[str], user_id: str = "guest_user") -> dict:
    """Temporarily holds selected seats for 10 minutes to allow checkout.
    
    Args:
        showtime_id: Screening showtime identifier.
        seats: List of seat codes to lock (e.g. ['F7', 'F8']).
        user_id: User account identifier.
        
    Returns:
        Dictionary with hold reservation token, expiration timestamp, and total cost breakdown.
    """
    availability = get_seat_availability(showtime_id)
    seat_map = {
        s["seat_id"]: s for row in availability["seat_grid"] for s in row["seats"]
    }
    
    # Validate requested seats
    for seat in seats:
        if seat not in seat_map:
            return {"success": False, "error": f"Seat '{seat}' does not exist in this auditorium."}
        if seat_map[seat]["status"] != "available":
            return {"success": False, "error": f"Seat '{seat}' is already occupied or held by another guest."}
            
    token = f"HLD-{uuid.uuid4().hex[:8].upper()}"
    unit_prices = [seat_map[s]["price"] for s in seats]
    subtotal = sum(unit_prices)
    booking_fee = 1.50 * len(seats)
    total = round(subtotal + booking_fee, 2)
    expires_at = time.time() + 600 # 10 minutes
    
    reservation_data = {
        "token": token,
        "showtime_id": showtime_id,
        "movie_title": availability["movie_title"],
        "cinema": availability["cinema"],
        "hall": availability["hall"],
        "date_time": availability["date_time"],
        "seats": seats,
        "subtotal": round(subtotal, 2),
        "booking_fee": round(booking_fee, 2),
        "total_amount": total,
        "user_id": user_id,
        "expires_at": expires_at
    }
    
    # Store in memory cache and persistent SQLite database
    ACTIVE_RESERVATIONS[token] = reservation_data
    try:
        get_booking_db().save_reservation_sync(reservation_data)
    except Exception:
        pass
    
    return {
        "success": True,
        "reservation_token": token,
        "movie_title": availability["movie_title"],
        "cinema": availability["cinema"],
        "date_time": availability["date_time"],
        "seats": seats,
        "total_amount": total,
        "expires_in_seconds": 600
    }


def process_ticket_payment(
    reservation_token: str,
    payment_method: str = "Google Pay",
    user_name: str = "Alex Morgan"
) -> dict:
    """Executes the transaction payment for held seats and issues confirmed digital tickets.
    
    Args:
        reservation_token: The temporary hold token returned by hold_seats_reservation.
        payment_method: Method used (e.g., 'Google Pay', 'Credit Card', 'Apple Pay').
        user_name: Name printed on ticket pass.
        
    Returns:
        Complete ticket booking receipt with confirmation number, QR barcode, and theater entry details.
    """
    res = ACTIVE_RESERVATIONS.get(reservation_token)
    if not res:
        try:
            res = get_booking_db().get_reservation_sync(reservation_token)
        except Exception:
            res = None

    if not res:
        return {"success": False, "error": "Invalid or expired reservation hold token."}
        
    if time.time() > res.get("expires_at", 0):
        if reservation_token in ACTIVE_RESERVATIONS:
            del ACTIVE_RESERVATIONS[reservation_token]
        try:
            get_booking_db().delete_reservation_sync(reservation_token)
        except Exception:
            pass
        return {"success": False, "error": "Reservation hold token has expired. Please re-select your seats."}
        
    booking_id = f"BK-{uuid.uuid4().hex[:6].upper()}"
    qr_code_token = f"PASS://CINEMA/{booking_id}/{res['showtime_id']}/{'-'.join(res['seats'])}"
    
    from datetime import timezone
    booking_record = {
        "success": True,
        "booking_id": booking_id,
        "showtime_id": res["showtime_id"],
        "movie_title": res["movie_title"],
        "cinema": res["cinema"],
        "hall": res["hall"],
        "date_time": res["date_time"],
        "seats": res["seats"],
        "number_of_tickets": len(res["seats"]),
        "total_amount": res["total_amount"],
        "payment_method": payment_method,
        "user_name": user_name,
        "qr_code_token": qr_code_token,
        "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "CONFIRMED"
    }
    
    # Persist booking to memory cache & SQLite database
    CONFIRMED_BOOKINGS[booking_id] = booking_record
    OCCUPIED_SEATS_MAP.setdefault(res["showtime_id"], []).extend(res["seats"])
    try:
        get_booking_db().save_booking_sync(booking_record)
        get_booking_db().add_occupied_seats_sync(res["showtime_id"], res["seats"], booking_id)
        get_booking_db().delete_reservation_sync(reservation_token)
    except Exception:
        pass
    
    # Remove temporary hold from cache
    if reservation_token in ACTIVE_RESERVATIONS:
        del ACTIVE_RESERVATIONS[reservation_token]
    
    return booking_record


def cancel_booking(booking_id: str) -> dict:
    """Cancels a confirmed cinema ticket booking and issues a refund.
    
    Args:
        booking_id: Booking confirmation number.
        
    Returns:
        Cancellation status and refund receipt.
    """
    booking = CONFIRMED_BOOKINGS.get(booking_id)
    if not booking:
        try:
            booking = get_booking_db().get_booking_sync(booking_id)
        except Exception:
            booking = None

    if not booking:
        return {"success": False, "error": f"Booking '{booking_id}' not found."}
        
    # Free up seats in memory and SQLite database
    showtime_id = booking.get("showtime_id")
    if showtime_id in OCCUPIED_SEATS_MAP:
        for seat in booking.get("seats", []):
            if seat in OCCUPIED_SEATS_MAP[showtime_id]:
                OCCUPIED_SEATS_MAP[showtime_id].remove(seat)

    try:
        get_booking_db().update_booking_status_sync(booking_id, "CANCELLED")
        if showtime_id:
            get_booking_db().remove_occupied_seats_sync(showtime_id, booking.get("seats", []))
    except Exception:
        pass
                
    booking["status"] = "CANCELLED"
    return {
        "success": True,
        "booking_id": booking_id,
        "refund_amount": booking["total_amount"],
        "status": "REFUNDED"
    }
