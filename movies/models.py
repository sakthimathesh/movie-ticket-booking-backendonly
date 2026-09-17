from django.db import models
from django.contrib.auth.models import User

class Movies(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(max_length=100)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    language = models.CharField(max_length=100)
    duration = models.CharField(max_length=20)
    genre = models.CharField(max_length=100)


def __str__(self):
    return self.name


class Seat(models.Model):
    movie = models.ForeignKey(
    Movies,
     on_delete=models.CASCADE,
     related_name="seats"
     )
    seat_number = models.CharField(max_length=5)
    booked = models.BooleanField(default = False)

def __str__ (self):
    return f"{self.movie.name} - {self.seat_number}"


class Booking(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    movie = models.ForeignKey(
        Movies,
        on_delete=models.CASCADE
    )

    seats = models.TextField()

    total_seats = models.IntegerField()

    ticket_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    booking_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.movie.name}"

class RegistrationOTP(models.Model):

    username = models.CharField(max_length=150)

    email = models.EmailField()

    password = models.CharField(max_length=128)

    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - OTP"