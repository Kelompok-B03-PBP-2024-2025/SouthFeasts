from django.urls import path
from dashboard import views
from dashboard.views import (makanan_list, makanan_create, makanan_delete, 
                             makanan_update, show_json, initialize_admin, restaurant_list, 
                             restaurant_menu, restaurant_update, makanan_update_resto, 
                             get_reviews, delete_review, get_reviews_resto, show_json_restaurant,
                             create_makanan_flutter, edit_makanan_flutter, delete_makanan_flutter, edit_restaurant_flutter)

app_name = 'dashboard'

urlpatterns = [
    path('initialize-admin/', initialize_admin, name='initialize_admin'),
    path('resto-list/', restaurant_list, name='restaurant_list'),
    path('resto-menu/<str:resto_name>/', restaurant_menu, name='restaurant_menu'),
    path('', makanan_list, name='makanan_list'),
    path('makanan-create/', makanan_create, name='makanan_create'),
    path('makanan-delete/<str:id>/', makanan_delete, name='makanan_delete'),
    path('makanan-update/<str:id>/', makanan_update, name='makanan_update'),
    path('makanan-update-resto/<str:id>/', makanan_update_resto, name='makanan_update_resto'),
    path('resto-update/<str:resto_name>/', restaurant_update, name='restaurant_update'),
    path('show-json/', show_json, name='show_json'),
    path('menu-item-reviews/<int:menu_item_id>/', get_reviews, name='menu_item_reviews'),
    path('menu-item-reviews-resto/<int:menu_item_id>/', get_reviews_resto, name='menu_item_reviews_resto'),
    path('delete-review/<int:review_id>/', delete_review, name='delete_review'),
    path('show-json-restaurant/', show_json_restaurant, name='show_json_restaurant'),
    path('create-makanan-flutter/', create_makanan_flutter, name='create_makanan_flutter'),
    path('edit-makanan-flutter/<str:id>/', edit_makanan_flutter, name='edit_makanan_flutter'),
    path('delete-makanan-flutter/<str:id>/', delete_makanan_flutter, name='delete_makanan_flutter'),
    path('edit-restaurant-flutter/<str:resto_name>/', edit_restaurant_flutter, name='edit_restaurant_flutter'),
]
