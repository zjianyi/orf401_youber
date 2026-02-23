from django import forms
from django.forms import ModelForm

from .models import DriverApplication, Event, RideOffer, RideRequest


class RideForm(forms.Form):
  city = forms.CharField(label='City', max_length=64, required=False)
  state = forms.CharField(label='State (2-letter code)', max_length=2, required=False)


class EventCodeForm(forms.Form):
  """
  Lets attendees enter an organizer-provided event code.
  """
  code = forms.CharField(label="Event code", max_length=12, required=True)


class DriverApplicationForm(ModelForm):
  """
  Driver application form shown from the homepage.
  """
  class Meta:
    model = DriverApplication
    fields = [
      "full_name",
      "email",
      "phone",
      "age",
      "car_type",
      "has_insurance",
      "insurance_provider",
      "driving_habits",
      "consent_to_background_check",
    ]

  def clean_age(self):
    age = self.cleaned_data.get("age")
    # Basic eligibility check; real logic can be expanded later.
    if age is not None and age < 18:
      raise forms.ValidationError("You must be at least 18 years old to apply.")
    return age


class OrganizerEventCreateForm(ModelForm):
  """
  Event organizer form for creating a new event with an invite code.
  """
  code = forms.CharField(
    label="Invite code (optional)",
    max_length=12,
    required=False,
    help_text="Leave blank to auto-generate a code."
  )

  class Meta:
    model = Event
    fields = [
      "name",
      "destination_name",
      "destination_address",
      "city",
      "category",
      "is_public",
      "start_time",
      "end_time",
      "code",
    ]

  def clean_code(self):
    code = (self.cleaned_data.get("code") or "").strip().upper()
    if code and len(code) < 4:
      raise forms.ValidationError("Invite code must be at least 4 characters.")
    return code


class PublicEventCreateForm(ModelForm):
  """
  Simple "create your event" form exposed from the homepage for custom trips.
  """
  class Meta:
    model = Event
    fields = [
      "name",
      "destination_name",
      "destination_address",
      "city",
      "is_public",
      "start_time",
      "end_time",
    ]


class AirportEventForm(ModelForm):
  """
  Airport flow: capture airport + flight so we can create or reuse an event.
  In a production system, flight details would be looked up via an external API.
  """
  class Meta:
    model = Event
    fields = [
      "airport_code",
      "flight_number",
      "destination_name",
      "start_time",
    ]


class RideOfferForm(ModelForm):
  """
  Driver flow: create a ride offer for an event.
  """
  class Meta:
    model = RideOffer
    fields = [
      "driver_name",
      "driver_contact",
      "pickup_label",
      "pickup_address",
      "pickup_lat",
      "pickup_lng",
      "seats_total",
      "depart_time",
      "duration_minutes",
      "driving_score",
    ]

  def clean_seats_total(self):
    seats = self.cleaned_data.get("seats_total")
    if seats is not None and seats < 1:
      raise forms.ValidationError("Seats must be at least 1.")
    return seats


class RideRequestForm(ModelForm):
  """
  Rider flow: request to join a specific ride offer.
  """
  class Meta:
    model = RideRequest
    fields = [
      "rider_name",
      "rider_contact",
      "passengers_count",
      "pickup_notes",
      "pickup_lat",
      "pickup_lng",
    ]

  def clean_passengers_count(self):
    n = self.cleaned_data.get("passengers_count")
    if n is not None and n < 1:
      raise forms.ValidationError("Passenger count must be at least 1.")
    return n

