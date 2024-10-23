from django.urls import path
from dashboard import views
from dashboard.views import makanan_list, makanan_create, is_admin, makanan_delete, makanan_update, show_xml, show_json, show_xml_by_id, show_json_by_id, initialize_admin
from dashboard.views import restaurant_list, restaurant_menu

app_name = 'dashboard'

urlpatterns = [
    path('initialize-admin/', initialize_admin, name='initialize_admin'),
    path('resto-list/', restaurant_list, name='restaurant_list'),
    path('resto-menu/<str:resto_name>/', restaurant_menu, name='restaurant_menu'),
    path('', makanan_list, name='makanan_list'),
    path('makanan-create/', makanan_create, name='makanan_create'),
    path('makanan-delete/<str:id>/', makanan_delete, name='makanan_delete'),
    path('makanan-update/<str:id>/', makanan_update, name='makanan_update'),
    path('show-xml/', show_xml, name='show_xml'),
    path('show-json/', show_json, name='show_json'),
    path('show-xml/<str:id>/', show_xml_by_id, name='show_xml_by_id'),
    path('show-json/<str:id>/', show_json_by_id, name='show_json_by_id'),
]