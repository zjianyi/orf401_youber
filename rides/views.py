from django.shortcuts import render
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

import random
import string

from .models import Person, Event, DriverApplication, RideOffer, RideRequest
from .forms import (
  RideForm,
  EventCodeForm,
  DriverApplicationForm,
  OrganizerEventCreateForm,
  RideOfferForm,
  RideRequestForm,
  PublicEventCreateForm,
  AirportEventForm,
)


def index(request):
  context = {}
  
  city = request.GET.get('city', '').strip()
  state = request.GET.get('state', '').strip()
  
  people = Person.objects.all()
  
  if city or state:
    context["inputExists"] = True
    
    query_filters = Q()
    
    if city:
      query_filters &= (
        Q(origination__icontains=city) | 
        Q(destination_city__icontains=city)
      )
    
    if state:
      query_filters &= Q(destination_state__iexact=state)
    
    people = people.filter(query_filters)
    
    context["search_city"] = city
    context["search_state"] = state.upper()
  
  context["people"] = people
  context["form"] = RideForm()

  return render(request, "index_view.html", context)


def home(request):
  """
  Marketing homepage: shows entry points plus a small "Events nearby" section.
  For now, "nearby" is implemented as a simple list of public events grouped
  by category; in a production system this could be filtered by location.
  """
  sports_events = Event.objects.filter(
    is_public=True, category=Event.CATEGORY_SPORTS
  ).order_by("-start_time", "-created_at")[:6]
  professional_events = Event.objects.filter(
    is_public=True, category=Event.CATEGORY_PROFESSIONAL
  ).order_by("-start_time", "-created_at")[:6]
  airport_events = Event.objects.filter(
    is_public=True, category=Event.CATEGORY_AIRPORT
  ).order_by("-start_time", "-created_at")[:6]

  context = {
    "sports_events": sports_events,
    "professional_events": professional_events,
    "airport_events": airport_events,
  }
  return render(request, "index.html", context)


def _generate_event_code(length=8):
  """
  Generates a short invite code for an Event.
  This is not intended to be guess-proof, but is treated like a secret.
  """
  alphabet = string.ascii_uppercase + string.digits
  return "".join(random.choice(alphabet) for _ in range(length))


def enter_event_code(request):
  """
  Attendee flow: enter a code from an organizer and redirect to the event portal.
  """
  # Support both GET (?code=XYZ) and POST.
  initial_code = (request.GET.get("code") or "").strip().upper()
  if request.method == "POST":
    form = EventCodeForm(request.POST)
    if form.is_valid():
      code = form.cleaned_data["code"].strip().upper()
      try:
        Event.objects.get(code=code)
        return redirect("event_portal", code=code)
      except Event.DoesNotExist:
        messages.error(request, "That event code was not found. Please check and try again.")
  else:
    if initial_code:
      # If code is valid, redirect immediately.
      if Event.objects.filter(code=initial_code).exists():
        return redirect("event_portal", code=initial_code)
    form = EventCodeForm(initial={"code": initial_code})

  return render(request, "event_code_enter.html", {"form": form})


def invite_link(request, token):
  """
  Invite-link access: a unique URL that resolves to an event portal.
  """
  event = get_object_or_404(Event, invite_token=token)
  return redirect("event_portal", code=event.code)


def event_portal(request, code):
  """
  After code entry, the user chooses to offer a ride or join a ride for this event.
  """
  event = get_object_or_404(Event, code=code.upper())
  return render(request, "event_portal.html", {"event": event})


def driver_apply(request):
  """
  Homepage flow: driver application intake.
  """
  if request.method == "POST":
    form = DriverApplicationForm(request.POST)
    if form.is_valid():
      form.save()
      return render(request, "driver_apply_thanks.html")
  else:
    form = DriverApplicationForm()

  return render(request, "driver_apply.html", {"form": form})


def offer_ride(request, code):
  """
  Driver flow: create a RideOffer for an event, then redirect to the driver's dashboard link.
  """
  event = get_object_or_404(Event, code=code.upper())

  if request.method == "POST":
    form = RideOfferForm(request.POST)
    if form.is_valid():
      offer = form.save(commit=False)
      offer.event = event
      # Initialize seats_available from seats_total on creation.
      offer.seats_available = offer.seats_total
      offer.save()
      return redirect("driver_dashboard", token=str(offer.manage_token))
  else:
    form = RideOfferForm()

  return render(request, "offer_ride.html", {"event": event, "form": form})


def join_ride(request, code):
  """
  Rider flow: show available ride offers for an event, plus a simple map.
  """
  event = get_object_or_404(Event, code=code.upper())
  offers = RideOffer.objects.filter(event=event, seats_available__gt=0).order_by("-created_at")
  return render(request, "join_ride.html", {"event": event, "offers": offers})


def request_join_ride(request, ride_id):
  """
  Rider flow: create a RideRequest for a specific RideOffer.
  """
  ride = get_object_or_404(RideOffer, id=ride_id)

  if request.method == "POST":
    form = RideRequestForm(request.POST)
    if form.is_valid():
      rr = form.save(commit=False)
      rr.ride = ride
      rr.save()
      return render(request, "ride_request_sent.html", {"event": ride.event, "ride": ride, "request_obj": rr})
  else:
    form = RideRequestForm()

  return render(request, "ride_request_form.html", {"event": ride.event, "ride": ride, "form": form})


def driver_dashboard(request, token):
  """
  Driver flow: dashboard for a specific RideOffer, accessed via a secret manage_token link.
  """
  offer = get_object_or_404(RideOffer, manage_token=token)

  # Small "live update": the page can auto-refresh via JS in the template.
  pending = offer.requests.filter(status=RideRequest.STATUS_PENDING).order_by("requested_at")
  accepted = offer.requests.filter(status=RideRequest.STATUS_ACCEPTED).order_by("requested_at")
  rejected = offer.requests.filter(status=RideRequest.STATUS_REJECTED).order_by("requested_at")

  return render(request, "driver_dashboard.html", {
    "offer": offer,
    "pending_requests": pending,
    "accepted_requests": accepted,
    "rejected_requests": rejected,
  })


def _dashboard_action_allowed(offer, request_obj):
  # Defensive check: only allow actions on requests for the same offer.
  return request_obj.ride_id == offer.id


def driver_request_action(request, token, request_id, action):
  """
  Driver flow: accept/reject a RideRequest.
  """
  offer = get_object_or_404(RideOffer, manage_token=token)
  rr = get_object_or_404(RideRequest, id=request_id)

  if request.method != "POST":
    return redirect("driver_dashboard", token=str(token))

  if not _dashboard_action_allowed(offer, rr):
    messages.error(request, "That request does not belong to this ride.")
    return redirect("driver_dashboard", token=str(token))

  if rr.status != RideRequest.STATUS_PENDING:
    messages.info(request, "That request is no longer pending.")
    return redirect("driver_dashboard", token=str(token))

  if action == "accept":
    if offer.seats_available < rr.passengers_count:
      messages.error(request, "Not enough seats available to accept this request.")
      return redirect("driver_dashboard", token=str(token))
    rr.status = RideRequest.STATUS_ACCEPTED
    rr.decided_at = timezone.now()
    rr.save()
    # Decrement remaining seats.
    offer.seats_available = offer.seats_available - rr.passengers_count
    offer.save()
    messages.success(request, "Request accepted.")
  elif action == "reject":
    rr.status = RideRequest.STATUS_REJECTED
    rr.decided_at = timezone.now()
    rr.save()
    messages.success(request, "Request rejected.")
  else:
    messages.error(request, "Unknown action.")

  return redirect("driver_dashboard", token=str(token))


def _is_staff(user):
  return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(_is_staff)
def organizer_event_create(request):
  """
  Organizer flow: staff-only event creation that outputs an invite code + invite link.
  """
  if request.method == "POST":
    form = OrganizerEventCreateForm(request.POST)
    if form.is_valid():
      event = form.save(commit=False)
      event.created_by = request.user
      # Organizer-created events default to public unless explicitly unchecked.
      if event.category == Event.CATEGORY_CUSTOM:
        event.category = Event.CATEGORY_PROFESSIONAL
      # If no code provided, generate a unique one.
      if not event.code:
        event.code = _generate_event_code()
      # Ensure uniqueness in case of collision.
      attempts = 0
      while Event.objects.filter(code=event.code).exists():
        attempts += 1
        if attempts > 10:
          form.add_error("code", "Could not generate a unique code. Please enter one manually.")
          return render(request, "organizer_event_create.html", {"form": form})
        event.code = _generate_event_code()
      event.code = event.code.upper()
      event.save()

      invite_url = request.build_absolute_uri(reverse("invite_link", kwargs={"token": str(event.invite_token)}))
      portal_url = request.build_absolute_uri(reverse("event_portal", kwargs={"code": event.code}))
      return render(request, "organizer_event_created.html", {
        "event": event,
        "invite_url": invite_url,
        "portal_url": portal_url,
      })
  else:
    form = OrganizerEventCreateForm()

  return render(request, "organizer_event_create.html", {"form": form})


def public_event_create(request):
  """
  Public "create your event" flow for ad-hoc events (e.g., trip from A to B).
  """
  if request.method == "POST":
    form = PublicEventCreateForm(request.POST)
    if form.is_valid():
      event = form.save(commit=False)
      # Treat these as custom events accessible via code/link.
      event.category = Event.CATEGORY_CUSTOM
      # Always generate a code for public-created events.
      event.code = _generate_event_code()
      # Ensure uniqueness in case of collision.
      while Event.objects.filter(code=event.code).exists():
        event.code = _generate_event_code()
      event.code = event.code.upper()
      event.save()

      portal_url = request.build_absolute_uri(reverse("event_portal", kwargs={"code": event.code}))
      return render(request, "organizer_event_created.html", {
        "event": event,
        "invite_url": portal_url,
        "portal_url": portal_url,
      })
  else:
    form = PublicEventCreateForm()

  return render(request, "public_event_create.html", {"form": form})


def airport_portal(request):
  """
  Airport-specific entry point: user enters airport and flight number.
  For now we simply create/find an Event tagged as an airport event.
  """
  if request.method == "POST":
    form = AirportEventForm(request.POST)
    if form.is_valid():
      airport_code = form.cleaned_data["airport_code"].upper().strip()
      flight_number = form.cleaned_data["flight_number"].upper().strip()

      # Try to reuse an existing airport event if one exists.
      event = Event.objects.filter(
        category=Event.CATEGORY_AIRPORT,
        airport_code=airport_code,
        flight_number=flight_number,
      ).order_by("-start_time", "-created_at").first()

      if not event:
        event = form.save(commit=False)
        event.category = Event.CATEGORY_AIRPORT
        event.airport_code = airport_code
        event.flight_number = flight_number
        event.name = event.name or f"Flight {flight_number} from {airport_code}"
        if not event.destination_name:
          event.destination_name = "Airport ride"
        # Always generate a code for airport events.
        event.code = _generate_event_code()
        while Event.objects.filter(code=event.code).exists():
          event.code = _generate_event_code()
        event.code = event.code.upper()
        event.is_public = True
        event.save()

      return redirect("event_portal", code=event.code)
  else:
    form = AirportEventForm()

  return render(request, "airport_portal.html", {"form": form})
