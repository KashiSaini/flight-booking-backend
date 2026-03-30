import os
import smtplib
import ssl
from email.message import EmailMessage

from shared.core.celery_app import celery_app


@celery_app.task(
    name="booking.send_booking_confirmation_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_booking_confirmation_email(
    to_email: str,
    booked_by: str,
    flight: dict,
    passengers: list[dict],
):
    if not to_email:
        raise ValueError("Recipient email is required to send booking confirmation")

    msg = EmailMessage()
    msg["Subject"] = f"Flight Booking Confirmation - {flight['source']} to {flight['destination']}"
    msg["From"] = os.getenv("MAIL_FROM")
    msg["To"] = to_email

    passenger_lines = []
    total_amount = 0.0

    for p in passengers:
        total_amount += float(p["price_paid"] or 0)
        passenger_lines.append(
            f"- {p['passenger_name']} | Seat: {p['seat_number']} | "
            f"Class: {p['seat_type']} | Destination: {p['destination']} | "
            f"Booking Ref: {p['booking_reference']} | Price: {p['price_paid']}"
        )

    body = f"""
Hello,

Your flight booking has been created successfully.

Booked By: {booked_by}
Flight ID: {flight['id']}
Airline: {flight.get('airline') or 'N/A'}
Route: {flight['source']} -> {flight['destination']}
Departure Time: {flight.get('departure_time') or 'N/A'}

Passengers:
{chr(10).join(passenger_lines)}

Total Amount: {total_amount}

Thank you.
"""

    msg.set_content(body)

    host = os.getenv("MAIL_HOST")
    port = int(os.getenv("MAIL_PORT", "587"))
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"

    context = ssl.create_default_context()

    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls(context=context)
        if username and password:
            server.login(username, password)
        server.send_message(msg)
