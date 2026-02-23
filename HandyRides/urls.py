"""HandyRides URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rides import views as rides_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('rides/', include('rides.urls')),
    # Auth endpoints for the "Event organizer log in" flow.
    path('accounts/', include('django.contrib.auth.urls')),

    # Event/code portal routes (kept at the project root for simple URLs).
    path('event/enter/', rides_views.enter_event_code, name='enter_event_code'),
    path('event/<str:code>/', rides_views.event_portal, name='event_portal'),
    path('event/<str:code>/offer/', rides_views.offer_ride, name='offer_ride'),
    path('event/<str:code>/join/', rides_views.join_ride, name='join_ride'),
    path('ride/<int:ride_id>/request/', rides_views.request_join_ride, name='request_join_ride'),

    # Driver dashboard (secret link).
    path('driver/dashboard/<uuid:token>/', rides_views.driver_dashboard, name='driver_dashboard'),
    path('driver/dashboard/<uuid:token>/request/<int:request_id>/<str:action>/',
         rides_views.driver_request_action, name='driver_request_action'),

    # Driver application.
    path('driver/apply/', rides_views.driver_apply, name='driver_apply'),

    # Organizer event creation (staff only).
    path('organizer/events/new/', rides_views.organizer_event_create, name='organizer_event_create'),
    path('invite/<uuid:token>/', rides_views.invite_link, name='invite_link'),

    # Public event creation and airport flows.
    path('events/create/', rides_views.public_event_create, name='public_event_create'),
    path('airport/', rides_views.airport_portal, name='airport_portal'),

    # Marketing homepage.
    path('', rides_views.home, name='home')
]
