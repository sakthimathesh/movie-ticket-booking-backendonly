from django.contrib import admin
from .models import Movies,Seat,Booking

admin.site.register(Movies)
admin.site.register(Seat)
admin.site.register(Booking)