"""Booking Agent for Cinema Outings.

Handles seat selection, temporary reservation holds, and payment transactions
using custom cinema transactional functions. Generates A2UI seat maps and ticket passes.
"""

from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent
from backend.config import DEFAULT_MODEL
from backend.tools.booking_transactions import (
    get_seat_availability,
    hold_seats_reservation,
    process_ticket_payment,
    cancel_booking
)
from backend.protocols.a2ui import (
    build_seat_map_component,
    build_ticket_pass_component,
    A2UIComponent
)
from backend.state.memory_manager import add_movie_to_seen_history

BOOKING_AGENT_INSTRUCTION = """You are the Booking Specialist Agent for Cinema Outings.
Your role is to guide guests through seat selection, holding seats, and completing ticket purchases.

Your Tools:
1. get_seat_availability: Inspect available vs occupied seats for a showtime.
2. hold_seats_reservation: Lock seats temporarily for 10 minutes.
3. process_ticket_payment: Charge payment and generate official ticket pass.
4. cancel_booking: Cancel booking and refund tickets.

Rules:
- Guide the user clearly on screen type, auditorium hall, and seat pricing.
- Once seats are chosen and held, confirm total price before transaction execution.
- Emits confirmed ticket passes upon purchase.
"""

def create_booking_agent(model: Optional[str] = None) -> LlmAgent:
    """Instantiates the Booking ADK Agent with deterministic model support."""
    selected_model = model or DEFAULT_MODEL
    return LlmAgent(
        name="BookingAgent",
        model=selected_model,
        description="Manages theater seating layouts, reservation holds, and ticket payment transactions.",
        instruction=BOOKING_AGENT_INSTRUCTION,
        tools=[
            get_seat_availability,
            hold_seats_reservation,
            process_ticket_payment,
            cancel_booking
        ],
        output_key="booking_result"
    )


class BookingService:
    """Service wrapper for Booking Agent workflows and A2UI generation."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.agent = create_booking_agent(model=self.model)

    def show_seats_for_showtime(
        self,
        showtime_id: str = "SH-DUNE-1930"
    ) -> Dict[str, Any]:
        """Fetches seat availability and generates an A2UI seat map component."""
        availability = get_seat_availability(showtime_id)
        component = build_seat_map_component(availability)
        return {
            "text": f"Here is the real-time seating chart for {availability['movie_title']} ({availability['hall']}) at {availability['date_time']}. Tap any available seat to select your spot!",
            "components": [component],
            "availability": availability
        }

    def hold_and_confirm_seats(
        self,
        showtime_id: str,
        seats: List[str],
        user_id: str = "user_default"
    ) -> Dict[str, Any]:
        """Holds seats and prompts for payment confirmation."""
        hold_res = hold_seats_reservation(showtime_id, seats, user_id=user_id)
        if not hold_res.get("success"):
            return {
                "text": f"Sorry, could not hold seats: {hold_res.get('error')}",
                "components": []
            }
            
        seats_str = ", ".join(seats)
        text = (
            f"Locked in seats {seats_str} for {hold_res['movie_title']}! "
            f"Total: ${hold_res['total_amount']:.2f}. "
            f"Would you like to complete this purchase via Google Pay?"
        )
        return {
            "text": text,
            "components": [],
            "reservation": hold_res
        }

    def complete_booking(
        self,
        reservation_token: str,
        payment_method: str = "Google Pay",
        user_name: str = "Alex Morgan",
        session_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executes payment transaction, produces A2UI ticket pass, and updates session state."""
        booking = process_ticket_payment(
            reservation_token=reservation_token,
            payment_method=payment_method,
            user_name=user_name
        )
        
        if not booking.get("success"):
            return {
                "text": f"Payment failed: {booking.get('error')}",
                "components": []
            }
            
        ticket_comp = build_ticket_pass_component(booking)
        
        # Update session memory
        if session_state is not None:
            session_state["active_booking"] = booking
            # A film is considered watched when a ticket has been purchased for it
            if booking.get("movie_title"):
                add_movie_to_seen_history(
                    session_state,
                    movie_title=booking["movie_title"],
                    cinema=booking.get("cinema", "Metropolis Cinema IMAX")
                )

        seats_str = ", ".join(booking["seats"])
        reply_text = (
            f"🎉 Success! Your booking is confirmed ({booking['booking_id']}). "
            f"Seats: {seats_str} for {booking['movie_title']} at {booking['cinema']}. "
            f"Your digital pass is ready below!"
        )
        
        return {
            "text": reply_text,
            "components": [ticket_comp],
            "booking": booking
        }
