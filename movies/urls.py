from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),

    path("register/send-otp/", views.send_otp, name="send_otp"),
    path("register/", views.register, name='register'),

    path("login/", views.login, name="login"),

    path("bookings/<str:username>/", views.booking_list, name="booking_list"),
    path("bookings/", views.create_booking, name="create_booking"),

    path("<int:id>/seats/", views.seat_list, name="seat_list"),
    path("<int:id>/", views.movie_detail, name='movie_detail'),

    path("import-movies/", views.import_movies, name="import_movies"),

    path("test-email/", views.test_email, name="test_email"),
    path("register/send-otp/", views.send_otp, name="send_otp"),
   path("register/verify-otp/", views.verify_otp, name="verify_otp"),
   path("register/", views.register, name="register"),
   path(
    "bookings/cancel/<int:booking_id>/",
    views.cancel_booking,
    name="cancel_booking"
),
]