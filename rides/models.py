from django.db import models
from django.contrib.auth.models import User
import uuid

# NOTE:
# This project started as a simple location-based "find registrants" demo.
# The models below extend it to support event-scoped ride sharing via invite codes.


class Person(models.Model):
  first_name = models.CharField(max_length=64)
  origination = models.CharField(max_length=64)
  destination_city = models.CharField(max_length=64)
  destination_state = models.CharField(max_length=2)
  date = models.DateField()
  time = models.TimeField()
  taking_passengers = models.BooleanField(default=False)
  seats_available = models.IntegerField(default=0)


class Event(models.Model):
  """
  An event that attendees can join using either a short invite code
  or a unique invite link token.
  """
  CATEGORY_SPORTS = "sports"
  CATEGORY_PROFESSIONAL = "professional"
  CATEGORY_CUSTOM = "custom"
  CATEGORY_AIRPORT = "airport"
  CATEGORY_CHOICES = [
    (CATEGORY_SPORTS, "Sports"),
    (CATEGORY_PROFESSIONAL, "Professional"),
    (CATEGORY_CUSTOM, "Custom / Personal"),
    (CATEGORY_AIRPORT, "Airport / Flight"),
  ]

  name = models.CharField(max_length=120)
  destination_name = models.CharField(max_length=120)
  destination_address = models.CharField(max_length=255, blank=True, default="")
  start_time = models.DateTimeField(null=True, blank=True)
  end_time = models.DateTimeField(null=True, blank=True)

   # Optional metadata used for "events nearby" and airport flows.
  category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_CUSTOM)
  city = models.CharField(max_length=120, blank=True, default="")
  is_public = models.BooleanField(default=True)

  # Airport-specific helpers (optional).
  airport_code = models.CharField(max_length=8, blank=True, default="")
  flight_number = models.CharField(max_length=20, blank=True, default="")

  # Short code shared by organizers (treated as a secret).
  code = models.CharField(max_length=12, unique=True)

  # Unique token for "invite link" access.
  invite_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

  created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.name} ({self.code})"


class DriverApplication(models.Model):
  """
  Captures driver application data so organizers/admins can review suitability.
  """
  STATUS_PENDING = "pending"
  STATUS_APPROVED = "approved"
  STATUS_REJECTED = "rejected"
  STATUS_CHOICES = [
    (STATUS_PENDING, "Pending"),
    (STATUS_APPROVED, "Approved"),
    (STATUS_REJECTED, "Rejected"),
  ]

  full_name = models.CharField(max_length=120)
  email = models.EmailField()
  phone = models.CharField(max_length=32, blank=True, default="")

  age = models.PositiveIntegerField()
  car_type = models.CharField(max_length=80)
  has_insurance = models.BooleanField(default=False)
  insurance_provider = models.CharField(max_length=120, blank=True, default="")
  driving_habits = models.TextField(blank=True, default="")

  # Minimal "secure process" acknowledgment.
  consent_to_background_check = models.BooleanField(default=False)

  status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
  submitted_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.full_name} ({self.status})"


class RideOffer(models.Model):
  """
  A driver offering seats for a given Event.
  The manage_token is used as a simple "driver dashboard secret link".
  """
  event = models.ForeignKey(Event, on_delete=models.CASCADE)

  driver_name = models.CharField(max_length=120)
  driver_contact = models.CharField(max_length=120, blank=True, default="")

  pickup_label = models.CharField(max_length=120)
  pickup_address = models.CharField(max_length=255, blank=True, default="")
  pickup_lat = models.FloatField(null=True, blank=True)
  pickup_lng = models.FloatField(null=True, blank=True)

  seats_total = models.PositiveIntegerField(default=1)
  seats_available = models.PositiveIntegerField(default=1)

  depart_time = models.DateTimeField(null=True, blank=True)
  duration_minutes = models.PositiveIntegerField(null=True, blank=True)

  driving_score = models.FloatField(default=5.0)

  manage_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"{self.event.code} - {self.driver_name} ({self.seats_available}/{self.seats_total})"


class RideRequest(models.Model):
  """
  A rider asking to join a RideOffer.
  """
  STATUS_PENDING = "pending"
  STATUS_ACCEPTED = "accepted"
  STATUS_REJECTED = "rejected"
  STATUS_CANCELLED = "cancelled"
  STATUS_CHOICES = [
    (STATUS_PENDING, "Pending"),
    (STATUS_ACCEPTED, "Accepted"),
    (STATUS_REJECTED, "Rejected"),
    (STATUS_CANCELLED, "Cancelled"),
  ]

  ride = models.ForeignKey(RideOffer, related_name="requests", on_delete=models.CASCADE)
  rider_name = models.CharField(max_length=120)
  rider_contact = models.CharField(max_length=120, blank=True, default="")

  passengers_count = models.PositiveIntegerField(default=1)
  pickup_notes = models.CharField(max_length=255, blank=True, default="")
  pickup_lat = models.FloatField(null=True, blank=True)
  pickup_lng = models.FloatField(null=True, blank=True)

  status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
  requested_at = models.DateTimeField(auto_now_add=True)
  decided_at = models.DateTimeField(null=True, blank=True)

  def __str__(self):
    return f"{self.ride.event.code} - {self.rider_name} ({self.status})"
