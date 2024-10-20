from django.urls import path
from main import views
from main.views import show_main

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('initialize-makanan/', views.initialize_makanan_data, name='initialize_makanan')
]