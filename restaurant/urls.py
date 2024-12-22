from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    # Fixed pattern by adding view function
    path('', views.restaurant_list, name='restaurant_list'),
    path('<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('show-json-restaurant/', views.show_json_restaurant, name='show_json_restaurant'),
    path('show-json-rsvp/<int:pk>', views.show_json_reservations, name='show_json_reservations'),
    path('get-restaurant/<int:pk>/', views.get_restaurant, name='get_restaurant'),
    path('create-reservation/<int:restaurant_id>/', views.create_reservation, name='create_reservation'),
    path('api/reservations/create/', views.create_reservation_api, name='create-reservation-api'),
]