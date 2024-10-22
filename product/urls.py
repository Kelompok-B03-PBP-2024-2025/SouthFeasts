# product/urls.py
from django.urls import path
from . import views

app_name = 'product'

urlpatterns = [
    path('', views.menu_catalog, name='menu_catalog'),
    path('<int:item_id>/', views.menu_detail, name='menu_detail'),
    path('restaurant/<int:restaurant_id>/menu/', views.restaurant_menu, name='restaurant_menu'),
    path('initialize-data/', views.initialize_data),
]

# from django.urls import path

# app_name = 'products'

# urlpatterns = [
    
    
# ]
