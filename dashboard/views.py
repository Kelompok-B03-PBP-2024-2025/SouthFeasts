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
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.core import serializers
from django.contrib.auth.models import User
from django.db.models import Count, Min, Max, Avg, F
from product.models import MenuItem
from restaurant.models import Restaurant
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.shortcuts import get_object_or_404
from review.models import ReviewEntry 
from .forms import MenuItemForm, RestaurantForm 

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
                    kecamatan=F('restaurant__kecamatan'),
                    location=F('restaurant__location')
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
    paginator = Paginator(makanans, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Format the data correctly
    formatted_makanans = [
        {
            'id': item.id,  # Use the actual ID from the MenuItem object
            'item': item.name,
            'description': item.description,
            'price': item.price,
            'image': item.image,
            'categories': item.category,
            'resto_name': item.resto_name,
            'kecamatan': item.kecamatan,
            'location': item.location,
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
    
    categories = menu_items.values_list('category', flat=True).distinct()
    
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
        for item in menu_items
    ]
    
    context = {
        'restaurant': {
            'resto_name': restaurant.name,
            'kecamatan': restaurant.kecamatan,
            'location': restaurant.location
        },
        'stats': stats,
        'menu_items': formatted_menu_items,
        'categories': categories,
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
@login_required(login_url='/authentication/login/')
def restaurant_update(request, resto_name):
    restaurant = Restaurant.objects.get(name=resto_name)
    
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('dashboard:restaurant_menu', resto_name=form.cleaned_data['name'])
    else:
        form = RestaurantForm(instance=restaurant)
    
    context = {
        'form': form,
        'restaurant': restaurant
    }
    return render(request, 'update_restaurant.html', context)

@csrf_exempt
@require_POST
@user_passes_test(is_admin)
def makanan_create(request):
    if request.method == 'POST':
        name = strip_tags(request.POST.get('name'))
        description = strip_tags(request.POST.get('description'))
        price = request.POST.get('price')
        image = strip_tags(request.POST.get('image'))
        category = strip_tags(request.POST.get('category'))
        resto_name = strip_tags(request.POST.get('resto_name'))
        kecamatan = strip_tags(request.POST.get('kecamatan'))
        location = strip_tags(request.POST.get('location'))

        # Create form instance with the POST data
        form_data = {
            'name': name,
            'description': description,
            'price': price,
            'image': image,
            'category': category,
            'resto_name': resto_name,
            'kecamatan': kecamatan,
            'location': location
        }
        
        form = MenuItemForm(form_data)
        
        if form.is_valid():
            form.save()
            return HttpResponse(b"CREATED", status=201)

    return HttpResponse(b"ERROR", status=400)

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


def makanan_update_resto(request, id):
    menu_item = MenuItem.objects.get(pk=id)
    form = MenuItemForm(request.POST or None, instance=menu_item)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(
            reverse('dashboard:restaurant_menu', 
                   kwargs={'resto_name': menu_item.restaurant.name})
        )
    context = {
        'form': form,
        'menu_item': menu_item
    }
    return render(request, 'update_makanan_resto.html', context)
    

@user_passes_test(is_admin)
def makanan_delete(request, id):
    menu_item = MenuItem.objects.get(pk=id)
    menu_item.delete()
    return redirect('dashboard:makanan_list')

def show_json(request):
    search_query = request.GET.get('search', '')
    selected_category = request.GET.get('category', 'all')
    selected_kecamatan = request.GET.get('kecamatan', 'all')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Query dasar
    menu_items = MenuItem.objects.all()

    # Filter berdasarkan pencarian
    if search_query:
        menu_items = menu_items.filter(name__icontains=search_query)

    # Filter berdasarkan kategori
    if selected_category != 'all':
        menu_items = menu_items.filter(category=selected_category)

    # Filter berdasarkan kecamatan
    if selected_kecamatan != 'all':
        menu_items = menu_items.filter(restaurant__kecamatan=selected_kecamatan)

    # Filter berdasarkan harga
    if min_price:
        menu_items = menu_items.filter(price__gte=min_price)
    if max_price:
        menu_items = menu_items.filter(price__lte=max_price)

    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 6
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (menu_items.count() + per_page - 1) // per_page
    menu_items = menu_items[start:end]

    # Tambahkan atribut 'current_page' di JSON response pada fungsi show_json
    data = {
        'results': [{
            'id': menu_item.id,
            'name': menu_item.name,
            'description': menu_item.description,
            'price': menu_item.price,
            'category': menu_item.category,
            'kecamatan': menu_item.restaurant.kecamatan,
            'image': menu_item.image,
            'restaurant_name': menu_item.restaurant.name,
            'location': menu_item.restaurant.location
        } for menu_item in menu_items],
        'total_pages': total_pages,
        'current_page': page,
        'has_previous': page > 1,
        'has_next': page < total_pages,
    }


    return JsonResponse(data)


@user_passes_test(is_admin)
def get_reviews(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    
    context = {
        'menu_item': menu_item,
        'reviews': reviews,
    }
    return render(request, 'review_list.html', context)

def get_reviews_resto(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    
    context = {
        'menu_item': menu_item,
        'reviews': reviews,
    }
    return render(request, 'review_list_resto.html', context)

@user_passes_test(is_admin)
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(ReviewEntry, id=review_id)
    menu_item_id = review.menu_item.id
    review.delete()
    
    # Redirect kembali ke halaman reviews
    return redirect('dashboard:menu_item_reviews', menu_item_id=menu_item_id)