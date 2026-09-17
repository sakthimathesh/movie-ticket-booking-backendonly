from django.http import JsonResponse
from .models import Movies, Seat, Booking ,RegistrationOTP
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
from django.db import transaction


# =========================
# MOVIE LIST
# =========================

def movie_list(request):

    movies = Movies.objects.all()

    movie_data = []

    for movie in movies:

        movie_data.append({
            'id': movie.id,
            'name': movie.name,
            'image': request.build_absolute_uri(movie.image.url),
            'rating': movie.rating,
            'language': movie.language,
            'duration': movie.duration,
            'genre': movie.genre
        })

    return JsonResponse(movie_data, safe=False)


# =========================
# MOVIE DETAIL
# =========================

def movie_detail(request, id):

    movie = get_object_or_404(
        Movies,
        id=id
    )

    return JsonResponse({
        'id': movie.id,
        'name': movie.name,
        'image': request.build_absolute_uri(movie.image.url),
        'rating': movie.rating,
        'language': movie.language,
        'duration': movie.duration,
        'genre': movie.genre
    })


# =========================
# SEAT LIST
# =========================

def seat_list(request, id):

    seats = Seat.objects.filter(
        movie_id=id
    )

    seat_data = []

    for seat in seats:

        seat_data.append({
            "seat_number": seat.seat_number,
            "booked": seat.booked
        })

    return JsonResponse(
        seat_data,
        safe=False
    )


# =========================
# REGISTER
# =========================

@csrf_exempt
def register(request):

    if request.method != "POST":

        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    data = json.loads(request.body)

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:

        return JsonResponse(
            {"message": "All fields are required"},
            status=400
        )

    if User.objects.filter(
        username=username
    ).exists():

        return JsonResponse(
            {"message": "Username already exists"},
            status=400
        )

    User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    return JsonResponse(
        {"message": "User Registered Successfully"},
        status=201
    )


# =========================
# LOGIN
# =========================

@csrf_exempt
def login(request):

    if request.method != "POST":

        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:

        return JsonResponse(
            {"message": "Username and password are required"},
            status=400
        )

    user = authenticate(
        username=username,
        password=password
    )

    if user is None:

        return JsonResponse(
            {"message": "Invalid username or password"},
            status=401
        )

    return JsonResponse(
        {
            "message": "Login successful",
            "username": user.username
        },
        status=200
    )


# =========================
# CREATE BOOKING
# =========================

# =========================
# CREATE BOOKING
# =========================

@csrf_exempt
def create_booking(request):

    if request.method != "POST":
        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    try:

        data = json.loads(request.body)

        username = data.get("username")
        movie_id = data.get("movieId")
        seats = data.get("seats")

        # Ticket price frontend-லிருந்து trust பண்ணக்கூடாது
        ticket_price = 200

        # =========================
        # REQUIRED DATA VALIDATION
        # =========================

        if not username or not movie_id or not seats:
            return JsonResponse(
                {"message": "Booking details are required"},
                status=400
            )

        # Seats must be a list
        if not isinstance(seats, list):
            return JsonResponse(
                {"message": "Invalid seat data"},
                status=400
            )

        # Empty seat list
        if len(seats) == 0:
            return JsonResponse(
                {"message": "Please select at least one seat"},
                status=400
            )

        # Maximum 10 seats
        if len(seats) > 10:
            return JsonResponse(
                {"message": "You can book a maximum of 10 seats"},
                status=400
            )

        # Duplicate seat check
        if len(seats) != len(set(seats)):
            return JsonResponse(
                {"message": "Duplicate seats are not allowed"},
                status=400
            )

        # =========================
        # USER VALIDATION
        # =========================

        try:
            user = User.objects.get(
                username=username
            )

        except User.DoesNotExist:

            return JsonResponse(
                {"message": "User not found"},
                status=404
            )

        # =========================
        # MOVIE VALIDATION
        # =========================

        try:
            movie = Movies.objects.get(
                id=movie_id
            )

        except Movies.DoesNotExist:

            return JsonResponse(
                {"message": "Movie not found"},
                status=404
            )

        # =========================
        # BOOKING TRANSACTION
        # =========================

        with transaction.atomic():

            seat_objects = []

            for seat_number in seats:

                try:

                    seat = Seat.objects.select_for_update().get(
                        movie=movie,
                        seat_number=seat_number
                    )

                except Seat.DoesNotExist:

                    return JsonResponse(
                        {
                            "message":
                            f"Seat {seat_number} does not exist"
                        },
                        status=400
                    )

                # Already booked check
                if seat.booked:

                    return JsonResponse(
                        {
                            "message":
                            f"Seat {seat_number} is already booked"
                        },
                        status=400
                    )

                seat_objects.append(seat)

            # =========================
            # CALCULATE AMOUNT
            # =========================

            total_seats = len(seats)

            total_amount = (
                total_seats * ticket_price
            )

            # =========================
            # CREATE BOOKING
            # =========================

            booking = Booking.objects.create(

                user=user,

                movie=movie,

                seats=", ".join(seats),

                total_seats=total_seats,

                ticket_price=ticket_price,

                total_amount=total_amount
            )

            # =========================
            # MARK SEATS AS BOOKED
            # =========================

            for seat in seat_objects:

                seat.booked = True

                seat.save(
                    update_fields=["booked"]
                )

        # =========================
        # SUCCESS RESPONSE
        # =========================

        return JsonResponse(

            {
                "message":
                "Booking saved successfully",

                "bookingId":
                booking.id
            },

            status=201
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {"message": "Invalid request data"},
            status=400
        )

    except Exception as error:

        print(
            "Booking Error:",
            repr(error)
        )

        return JsonResponse(
            {
                "message":
                "Booking failed. Please try again."
            },
            status=500
        )
# =========================
# BOOKING HISTORY
# =========================

def booking_list(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    bookings = Booking.objects.filter(
        user=user
    )

    booking_data = []

    for booking in bookings:

        booking_data.append({

            "id": booking.id,

            "movie": booking.movie.name,

            "seats": booking.seats,

            "total_seats": booking.total_seats,

            "ticket_price": booking.ticket_price,

            "total_amount": booking.total_amount
        })

    return JsonResponse(
        booking_data,
        safe=False
    )



# =========================
# BOOKING HISTORY
# =========================

def booking_list(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    bookings = Booking.objects.filter(
        user=user
    )

    booking_data = []

    for booking in bookings:

        booking_data.append({

            "id": booking.id,

            "movie": booking.movie.name,

            "seats": booking.seats,

            "total_seats": booking.total_seats,

            "ticket_price": booking.ticket_price,

            "total_amount": booking.total_amount

        })

    return JsonResponse(
        booking_data,
        safe=False
    )

# =========================
# TEST EMAIL
# =========================


@csrf_exempt
def test_email(request):

    if request.method != "POST":
        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    print("MAILERS:", settings.MAILERS)

    try:
        send_mail(
            "Movie Ticket Booking - Test Email",
            "Hello! This is a test email from Django.",
            settings.DEFAULT_FROM_EMAIL,
            ["sakthilegent003@gmail.com"],
        )

        return JsonResponse(
            {"message": "Test email sent successfully"},
            status=200
        )

    except Exception as error:
        print("Email Error:", repr(error))

        return JsonResponse(
            {
                "message": "Email sending failed",
                "error": str(error)
            },
            status=500
        )
@csrf_exempt
def send_otp(request):

    if request.method != "POST":
        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:
            return JsonResponse(
                {"message": "All fields are required"},
                status=400
            )

        # Check existing username
        if User.objects.filter(username=username).exists():
            return JsonResponse(
                {"message": "Username already exists"},
                status=400
            )

        # Check existing email
        if User.objects.filter(email=email).exists():
            return JsonResponse(
                {"message": "Email already registered"},
                status=400
            )

        # Generate 6 digit OTP
        otp = str(random.randint(100000, 999999))

        # Remove old OTPs for this email
        RegistrationOTP.objects.filter(email=email).delete()

        # Save OTP
        RegistrationOTP.objects.create(
            username=username,
            email=email,
            password=password,
            otp=otp
        )

        # Send OTP email
        send_mail(
            "Movie Ticket Booking - Email Verification",
            f"""
Hello {username},

Your OTP for Movie Ticket Booking registration is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

Thank you.
Movie Ticket Booking Team
""",
            None,
            [email],
        )

        return JsonResponse(
            {"message": "OTP sent successfully"},
            status=200
        )

    except Exception as error:

        print("OTP Error:", error)

        return JsonResponse(
            {
                "message": "Failed to send OTP"
            },
            status=500
        )

@csrf_exempt
def verify_otp(request):

    if request.method != "POST":
        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)

        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            return JsonResponse(
                {"message": "Email and OTP are required"},
                status=400
            )

        # Find OTP record
        otp_record = RegistrationOTP.objects.filter(
            email=email,
            otp=otp
        ).first()

        if not otp_record:
            return JsonResponse(
                {"message": "Invalid OTP"},
                status=400
            )

        # Check OTP expiry - 5 minutes
        expiry_time = otp_record.created_at + timedelta(minutes=5)

        if timezone.now() > expiry_time:
            otp_record.delete()

            return JsonResponse(
                {"message": "OTP expired. Please request a new OTP"},
                status=400
            )

        # Check username again
        if User.objects.filter(
            username=otp_record.username
        ).exists():
            otp_record.delete()

            return JsonResponse(
                {"message": "Username already exists"},
                status=400
            )

        # Create user
        User.objects.create_user(
            username=otp_record.username,
            email=otp_record.email,
            password=otp_record.password
        )

        # Delete OTP after successful registration
        otp_record.delete()

        return JsonResponse(
            {"message": "Registration successful"},
            status=201
        )

    except Exception as error:

        print("Verify OTP Error:", error)

        return JsonResponse(
            {"message": "OTP verification failed"},
            status=500
        )

@csrf_exempt
def cancel_booking(request, booking_id):

    if request.method != "DELETE":
        return JsonResponse({
            "message": "Only DELETE method allowed"
        }, status=405)

    try:

        with transaction.atomic():

            # Booking get
            booking = Booking.objects.select_for_update().get(
                id=booking_id
            )

            # Booking-la save pannirukkura seats
            seat_numbers = [
                seat.strip()
                for seat in booking.seats.split(",")
                if seat.strip()
            ]

            # Seats-ah release pannuvom
            Seat.objects.filter(
                movie=booking.movie,
                seat_number__in=seat_numbers
            ).update(
                booked=False
            )

            # Booking delete
            booking.delete()

        return JsonResponse({
            "message": "Booking cancelled successfully"
        }, status=200)

    except Booking.DoesNotExist:

        return JsonResponse({
            "message": "Booking not found"
        }, status=404)

    except Exception as error:

        print("Cancel Booking Error:", error)

        return JsonResponse({
            "message": "Unable to cancel booking"
        }, status=500)





















@csrf_exempt
def import_movies(request):

    if request.method != "POST":
        return JsonResponse(
            {"message": "Only POST method allowed"},
            status=405
        )

    try:
        data = json.loads(request.body)

        for item in data:
            Movies.objects.update_or_create(
                id=item["id"],
                defaults={
                    "name": item["name"],
                    "image": item["image"],
                    "rating": item["rating"],
                    "language": item["language"],
                    "duration": item["duration"],
                    "genre": item["genre"],
                }
            )

        return JsonResponse({
            "message": "Movies imported successfully",
            "count": len(data)
        })

    except Exception as error:
        return JsonResponse({
            "message": "Import failed",
            "error": str(error)
        }, status=500)