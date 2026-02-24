from django.urls import path

from . import views

app_name = 'rides'
urlpatterns = [
    path('', views.index, name='index'),
    path('person/<int:person_id>/join/', views.request_person_ride, name='request_person_ride'),
]
