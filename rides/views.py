from django.shortcuts import render
from django.db.models import Q

from .models import Person
from .forms import RideForm


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
