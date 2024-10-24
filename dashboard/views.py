# views.py
import csv
import os
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect
from django.urls import reverse
from authentication.models import UserProfile
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core import serializers
from django.contrib.auth.models import User
from django.db.models import Count, Min, Max, Avg, F
from product.models import MenuItem
from restaurant.models import Restaurant
from .forms import MenuItemForm

def initialize_admin(request):
    # Check if 'admin' user exists
    if User.objects.filter(username='admin').exists():
        User.objects.filter(username='admin').delete()
    
    user = User.objects.create_user(username='admin', password='admin')
    user.is_staff = True
    profile = UserProfile.objects.create(
        user=user,
        user_type='ADMIN',
        username='admin',
        fullname='Administrator',
        country='Indonesia'
    )
    user.save()
    profile.save()
    return HttpResponse("Admin berhasil diinisialisasi.")

def is_admin(user):
    return user.is_authenticated and user.userprofile.user_type == 'ADMIN'


@user_passes_test(is_admin)
@login_required(login_url='/authentication/login/')
def makanan_list(request):
    # Ambil kategori yang benar-benar digunakan dan hitung jumlahnya
    used_categories = (MenuItem.objects
                      .values('category')
                      .annotate(count=Count('category'))
                      .filter(count__gt=0)
                      .order_by('-count')
                      .values_list('category', flat=True)[:5])
    
    # Ambil kecamatan yang benar-benar memiliki restoran dengan menu
    used_kecamatans = (Restaurant.objects
                      .filter(menu_items__isnull=False)
                      .values('kecamatan')
                      .annotate(count=Count('menu_items', distinct=True))
                      .filter(count__gt=0)
                      .order_by('-count')
                      .values_list('kecamatan', flat=True)[:9])
    
    # Query utama untuk makanan
    makanans = (MenuItem.objects
                .select_related('restaurant')
                .annotate(
                    resto_name=F('restaurant__name'),
                    kecamatan=F('restaurant__kecamatan')
                )
                .values(
                    'id',
                    'name',
                    'description',
                    'price',
                    'image',
                    'category',
                    'resto_name',
                    'kecamatan'
                ))
    
    # Filter berdasarkan input user
    category = request.GET.get('category')
    kecamatan = request.GET.get('kecamatan')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('search')
    
    if category and category != 'all':
        if category in used_categories:
            makanans = makanans.filter(category=category)
    
    if kecamatan and kecamatan != 'all':
        if kecamatan in used_kecamatans:
            makanans = makanans.filter(restaurant__kecamatan=kecamatan)
    
    if min_price:
        makanans = makanans.filter(price__gte=min_price)
    
    if max_price:
        makanans = makanans.filter(price__lte=max_price)
    
    if search_query:
        makanans = makanans.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(list(makanans), 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Format the data correctly
    formatted_makanans = [
        {
            'id': item['id'],
            'item': item['name'],
            'description': item['description'],
            'price': item['price'],
            'image': item['image'],
            'categories': item['category'],
            'resto_name': item['resto_name'],
            'kecamatan': item['kecamatan'],
        }
        for item in page_obj
    ]
    
    context = {
        'makanans': formatted_makanans,
        'page_obj': page_obj,
        'categories': used_categories,
        'kecamatans': used_kecamatans,
        'selected_category': category,
        'selected_kecamatan': kecamatan,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
    }
    
    return render(request, 'makanan_list.html', context)

@user_passes_test(is_admin)
@login_required(login_url='/authentication/login/')
def restaurant_menu(request, resto_name):
    restaurant = Restaurant.objects.filter(name=resto_name).first()
    
    if not restaurant:
        raise Http404("Restaurant not found")
    
    stats = (MenuItem.objects
             .filter(restaurant=restaurant)
             .aggregate(
                 menu_count=Count('id'),
                 min_price=Min('price'),
                 max_price=Max('price'),
                 avg_price=Avg('price')
             ))
    
    menu_items = MenuItem.objects.filter(restaurant=restaurant)
    
    # Filter based on user input
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('search')
    
    if category and category != 'all':
        menu_items = menu_items.filter(category=category)
    
    if min_price:
        menu_items = menu_items.filter(price__gte=min_price)
    
    if max_price:
        menu_items = menu_items.filter(price__lte=max_price)
    
    if search_query:
        menu_items = menu_items.filter(name__icontains=search_query)
    
    categories = menu_items.values_list('category', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(list(menu_items), 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Format the data correctly
    formatted_menu_items = [
        {
            'id': item.id,
            'item': item.name,
            'description': item.description,
            'price': item.price,
            'image': item.image,
            'categories': item.category,
            'resto_name': restaurant.name,
            'kecamatan': restaurant.kecamatan,
        }
        for item in page_obj
    ]
    
    context = {
        'restaurant': {
            'resto_name': restaurant.name,
            'kecamatan': restaurant.kecamatan,
            'location': restaurant.location
        },
        'stats': stats,
        'menu_items': formatted_menu_items,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
    }
    
    return render(request, 'resto_menu.html', context)

@user_passes_test(is_admin)
@login_required(login_url='/authentication/login/')
def restaurant_list(request):
    # Base query with annotations
    restaurants = Restaurant.objects.annotate(
        menu_count=Count('menu_items'),
        min_price=Min('menu_items__price'),
        max_price=Max('menu_items__price'),
        image=Min('menu_items__image'),
        resto_name=F('name'),
    )
    
    # Get filter parameters
    kecamatan = request.GET.get('kecamatan')
    search_query = request.GET.get('search', '').strip()
    
    # Apply filters
    if kecamatan and kecamatan != 'all':
        restaurants = restaurants.filter(kecamatan__iexact=kecamatan)
    
    if search_query:
        restaurants = restaurants.filter(name__icontains=search_query)
    
    # Order results
    restaurants = restaurants.order_by('name')
    
    # Get unique kecamatan values for filter dropdown
    kecamatans = (Restaurant.objects
                  .values_list('kecamatan', flat=True)
                  .distinct()
                  .order_by('kecamatan'))
    
    # Paginate results
    paginator = Paginator(restaurants, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'restaurants': page_obj,
        'kecamatans': kecamatans,
        'selected_kecamatan': kecamatan,
        'search_query': search_query,
    }
    
    return render(request, 'resto_list.html', context)

@user_passes_test(is_admin)
def makanan_create(request):
    form = MenuItemForm(request.POST or None)
    if form.is_valid() and request.method == 'POST':
        menu_item = form.save(commit=False)
        menu_item.save()
        return redirect('dashboard:makanan_list')
    context = {
        'form': form
    }
    return render(request, 'create_makanan.html', context)

@user_passes_test(is_admin)
def makanan_update(request, id):
    menu_item = MenuItem.objects.get(pk=id)
    form = MenuItemForm(request.POST or None, instance=menu_item)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('dashboard:makanan_list'))
    context = {
        'form': form
    }
    return render(request, 'update_makanan.html', context)

@user_passes_test(is_admin)
def makanan_delete(request, id):
    menu_item = MenuItem.objects.get(pk=id)
    menu_item.delete()
    return redirect('dashboard:makanan_list')

def show_xml(request):
    data = MenuItem.objects.all()
    return HttpResponse(serializers.serialize("xml", data), content_type="application/xml")

def show_json(request):
    data = MenuItem.objects.all()
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def show_xml_by_id(request, id):
    data = MenuItem.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("xml", data), content_type="application/xml")

def show_json_by_id(request, id):
    data = MenuItem.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")