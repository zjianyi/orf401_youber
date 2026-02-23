from django.contrib import admin

from .models import Event, DriverApplication, RideOffer, RideRequest, Person

# Basic registrations to make it easy to manage in Django admin.
admin.site.register(Person)
admin.site.register(Event)
admin.site.register(DriverApplication)
admin.site.register(RideOffer)
admin.site.register(RideRequest)
