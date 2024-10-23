from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('', views.all_reviews, name='all_reviews'),  
    path('create/<int:item_id>/', views.create_review, name='create_review'),
]
