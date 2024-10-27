from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('', views.all_reviews, name='all_reviews'),
    path('create/<int:item_id>/', views.create_review, name='create_review'),
    path('<int:review_id>/', views.review_detail, name='review_detail'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    # path('create-ajax/<int:item_id>/', views.create_review_ajax, name='create_review_ajax'),
    path('json/', views.show_json, name='show_json'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
]