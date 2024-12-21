# views.py
import csv
import json
import os
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse
from authentication.models import UserProfile
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
    # Membuat user admin baru (menghapus yang lama jika ada)
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

def makanan_list(request):
    # Mengambil 5 kategori makanan 
    used_categories = (MenuItem.objects
                      .values_list('category', flat=True)
                      .distinct()
                      .order_by('category'))
    
    # Mengambil 9 kecamatan 
    used_kecamatans = (Restaurant.objects
                  .values_list('kecamatan', flat=True)
                  .distinct()
                  .order_by('kecamatan'))
    
    # Query untuk mengambil semua makanan dengan informasi restoran
    makanans = (MenuItem.objects
                .select_related('restaurant')
                .annotate(
                    resto_name=F('restaurant__name'),
                    kecamatan=F('restaurant__kecamatan'),
                    location=F('restaurant__location')
                ))
    
    # Menerapkan filter dari request
    category = request.GET.get('category')
    kecamatan = request.GET.get('kecamatan')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('search')
    
    # Filter berdasarkan kategori jika valid
    if category and category != 'all':
        if category in used_categories:
            makanans = makanans.filter(category=category)
    
    # Filter berdasarkan kecamatan jika valid
    if kecamatan and kecamatan != 'all':
        if kecamatan in used_kecamatans:
            makanans = makanans.filter(restaurant__kecamatan=kecamatan)
    
    # Filter berdasarkan harga
    if min_price:
        makanans = makanans.filter(price__gte=min_price)
    
    if max_price:
        makanans = makanans.filter(price__lte=max_price)
    
    # Filter berdasarkan pencarian nama
    if search_query:
        makanans = makanans.filter(name__icontains=search_query)
    
    # Paginasi: 9 item per halaman
    paginator = Paginator(makanans, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Format data untuk template
    formatted_makanans = [
        {
            'id': item.id,
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

def restaurant_menu(request, resto_name):
    # Mengambil detail restoran berdasarkan nama
    restaurant = Restaurant.objects.filter(name=resto_name).first()
    
    if not restaurant:
        raise Http404("Restaurant not found")
    
    # Mengambil statistik menu restoran
    stats = (MenuItem.objects
             .filter(restaurant=restaurant)
             .aggregate(
                 menu_count=Count('id'),
                 min_price=Min('price'),
                 max_price=Max('price'),
                 avg_price=Avg('price')
             ))
    
    # Mengambil semua menu dari restoran
    menu_items = MenuItem.objects.filter(restaurant=restaurant)
    categories = menu_items.values_list('category', flat=True).distinct()
    
    # Format data menu untuk template
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

def restaurant_list(request):
    # Query restoran dengan statistik menu
    restaurants = Restaurant.objects.annotate(
        menu_count=Count('menu_items'),
        min_price=Min('menu_items__price'),
        max_price=Max('menu_items__price'),
        image=Min('menu_items__image'),
        resto_name=F('name'),
    )
    
    # Filter berdasarkan request
    kecamatan = request.GET.get('kecamatan')
    search_query = request.GET.get('search', '').strip()
    
    if kecamatan and kecamatan != 'all':
        restaurants = restaurants.filter(kecamatan__iexact=kecamatan)
    
    if search_query:
        restaurants = restaurants.filter(name__icontains=search_query)
    
    restaurants = restaurants.order_by('name')
    
    # Mengambil daftar kecamatan untuk filter
    kecamatans = (Restaurant.objects
                  .values_list('kecamatan', flat=True)
                  .distinct()
                  .order_by('kecamatan'))
    
    # Paginasi: 9 restoran per halaman
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

def restaurant_update(request, resto_name):
    # Update informasi restoran
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
def makanan_create(request):
    # Membuat menu baru dengan validasi input
    if request.method == 'POST':
        name = strip_tags(request.POST.get('name'))
        description = strip_tags(request.POST.get('description'))
        price = request.POST.get('price')
        image = strip_tags(request.POST.get('image'))
        category = strip_tags(request.POST.get('category'))
        resto_name = strip_tags(request.POST.get('resto_name'))
        kecamatan = strip_tags(request.POST.get('kecamatan'))
        location = strip_tags(request.POST.get('location'))

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

def makanan_update(request, id):
    # Update menu dari halaman list
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
    # Update menu dari halaman restoran
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
    
def makanan_delete(request, id):
    # Hapus menu
    menu_item = MenuItem.objects.get(pk=id)
    menu_item.delete()
    return redirect('dashboard:makanan_list')

def show_json(request):
    # API endpoint untuk data makanan
    search_query = request.GET.get('search', '')
    selected_category = request.GET.get('category', 'all')
    selected_kecamatan = request.GET.get('kecamatan', 'all')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    menu_items = MenuItem.objects.all()

    # Get distinct categories and kecamatans
    categories = list(MenuItem.objects.values_list('category', flat=True).distinct())
    kecamatans = list(MenuItem.objects.values_list('restaurant__kecamatan', flat=True).distinct())

    # Terapkan filter
    if search_query:
        menu_items = menu_items.filter(name__icontains=search_query)

    if selected_category != 'all':
        menu_items = menu_items.filter(category=selected_category)

    if selected_kecamatan != 'all':
        menu_items = menu_items.filter(restaurant__kecamatan=selected_kecamatan)

    if min_price:
        menu_items = menu_items.filter(price__gte=min_price)
    if max_price:
        menu_items = menu_items.filter(price__lte=max_price)

    # Paginasi: 6 item per halaman
    page = int(request.GET.get('page', 1))
    per_page = 6
    start = (page - 1) * per_page
    end = start + per_page
    total_pages = (menu_items.count() + per_page - 1) // per_page
    menu_items = menu_items[start:end]

    # Format response JSON
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
            'location': menu_item.restaurant.location,
            'restaurant_id': menu_item.restaurant.id
        } for menu_item in menu_items],
        'total_pages': total_pages,
        'current_page': page,
        'has_previous': page > 1,
        'has_next': page < total_pages,
        'categories': categories,  # Add categories list
        'kecamatans': kecamatans  # Add kecamatans list
    }

    return JsonResponse(data)


def get_reviews(request, menu_item_id):
    # Tampilkan review untuk menu dari halaman list
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    
    context = {
        'menu_item': menu_item,
        'reviews': reviews,
    }
    return render(request, 'review_list.html', context)

def get_reviews_flutter(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    review_data = []
    for review in reviews:
        review_data.append({
            "id": review.id,
            "user": review.user.username if review.user else "Anonymous",
            "content": review.review_text,  # Changed here
            "rating": review.rating,
            "image": review.review_image.url if review.review_image else None,
            "created_at": review.created_at.isoformat(),
        })
    return JsonResponse({
        "status": "success",
        "menu_item_id": menu_item_id,
        "reviews": review_data,
    })

def get_reviews_resto(request, menu_item_id):
    # Tampilkan review untuk menu dari halaman restoran
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    reviews = ReviewEntry.objects.filter(menu_item=menu_item).select_related('user')
    
    context = {
        'menu_item': menu_item,
        'reviews': reviews,
    }
    return render(request, 'review_list_resto.html', context)

@require_POST
def delete_review(request, review_id):
    # Hapus review
    review = get_object_or_404(ReviewEntry, id=review_id)
    menu_item_id = review.menu_item.id
    review.delete()
    return redirect('dashboard:menu_item_reviews', menu_item_id=menu_item_id)

@csrf_exempt
def delete_review_flutter(request, review_id):
    if request.method == 'GET':
        try:
            review = get_object_or_404(ReviewEntry, pk=review_id)
            review.delete()
            return JsonResponse({
                "status": "success",
                "message": "Review deleted successfully"
            }, status=200)
        except ReviewEntry.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Review not found"
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)

def remove_empty_restaurants():
    # Hapus restoran tanpa menu
    Restaurant.objects.annotate(menu_count=Count('menu_items')).filter(menu_count=0).delete()

def show_json_restaurant(request):
    # API endpoint untuk data restoran

    # Query restoran dengan statistik menu
    restaurants = Restaurant.objects.annotate(
        menu_count=Count('menu_items'),
        min_price=Min('menu_items__price'),
        max_price=Max('menu_items__price'),
        image=Min('menu_items__image'),
        resto_name=F('name'),
    )
    remove_empty_restaurants() # Hapus restoran tanpa menu
    
    # Filter berdasarkan request
    kecamatan = request.GET.get('kecamatan')
    search_query = request.GET.get('search', '').strip()
    
    # Terapkan filter
    if kecamatan and kecamatan != 'all':
        restaurants = restaurants.filter(kecamatan__iexact=kecamatan)
    
    if search_query:
        restaurants = restaurants.filter(name__icontains=search_query)
    
    # Urutkan berdasarkan nama
    restaurants = restaurants.order_by('name')
    
    # Ambil daftar kecamatan untuk filter
    kecamatans = (Restaurant.objects
                  .values_list('kecamatan', flat=True)
                  .distinct()
                  .order_by('kecamatan'))
    
    # Paginasi: 9 restoran per halaman
    paginator = Paginator(restaurants, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Format data untuk response JSON
    restaurants_data = []
    for restaurant in page_obj:
        stats = (MenuItem.objects
                 .filter(restaurant=restaurant)
                 .aggregate(
                     menu_count=Count('id'),
                     min_price=Min('price'),
                     max_price=Max('price'),
                     avg_price=Avg('price')
                 ))
        restaurants_data.append({
            'id': restaurant.id,
            'name': restaurant.resto_name,
            'kecamatan': restaurant.kecamatan,
            'location': restaurant.location,
            'menu_count': stats['menu_count'],
            'min_price': stats['min_price'],
            'max_price': stats['max_price'],
            'avg_price': stats['avg_price'],
            'image': restaurant.image,
            'menus': [{
                'id': menu.id,
                'name': menu.name,
                'price': menu.price,
                'image': menu.image,
            } for menu in restaurant.menu_items.all()]
        })
    
    # Tambahan informasi paginasi
    data = {
        'restaurants': restaurants_data,
        'kecamatans': list(kecamatans),
        'selected_kecamatan': kecamatan,
        'search_query': search_query,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
    }
    
    return JsonResponse(data)

@csrf_exempt
def create_makanan_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get or create restaurant
            restaurant, created = Restaurant.objects.get_or_create(
                name=data['restaurant_name'],
                defaults={
                    'kecamatan': data['kecamatan'],
                    'location': data['location']
                }
            )
            
            # Create menu item
            menu_item = MenuItem.objects.create(
                name=data['name'],
                description=data['description'],
                price=int(data['price']),
                image=data['image'],
                category=data['category'],
                restaurant=restaurant
            )
            
            return JsonResponse({
                "status": "success",
                "message": "Menu item created successfully"
            }, status=201)
            
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
    
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)

@csrf_exempt
def edit_makanan_flutter(request, id):
    if request.method == 'POST':
        try:
            menu_item = MenuItem.objects.get(pk=id)
            data = json.loads(request.body)
            
            # Update restaurant info if provided
            if all(key in data for key in ['restaurant_name', 'kecamatan', 'location']):
                restaurant = menu_item.restaurant
                restaurant.name = data['restaurant_name']
                restaurant.kecamatan = data['kecamatan']
                restaurant.location = data['location']
                restaurant.save()
            
            # Update menu item fields
            menu_item.name = data.get('name', menu_item.name)
            menu_item.description = data.get('description', menu_item.description)
            menu_item.price = float(data.get('price', menu_item.price))
            menu_item.image = data.get('image', menu_item.image)
            menu_item.category = data.get('category', menu_item.category)
            menu_item.save()
            
            return JsonResponse({
                "status": "success",
                "message": "Menu item updated successfully"
            }, status=200)
            
        except MenuItem.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Menu item not found"
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
    
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)

@csrf_exempt
def delete_makanan_flutter(request, id):
    if request.method == 'GET':
        try:
            menu_item = MenuItem.objects.get(pk=id)
            menu_item.delete()

            return JsonResponse({
                "status": "success",
                "message": "Menu item deleted successfully"
            }, status=200)
            
        except MenuItem.DoesNotExist:
            return JsonResponse({
                "status": "error", 
                "message": "Menu item not found"
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
            
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)

@csrf_exempt
def edit_restaurant_flutter(request, resto_name):
    if request.method == 'POST':
        try:
            restaurant = Restaurant.objects.get(name=resto_name)
            data = json.loads(request.body)
            
            # Update restaurant fields
            restaurant.name = data.get('name', restaurant.name)
            restaurant.kecamatan = data.get('kecamatan', restaurant.kecamatan)
            restaurant.location = data.get('location', restaurant.location)
            restaurant.save()
            
            return JsonResponse({
                "status": "success",
                "message": "Restaurant updated successfully",
                "data": {
                    "name": restaurant.name,
                    "kecamatan": restaurant.kecamatan,
                    "location": restaurant.location
                }
            }, status=200)
            
        except Restaurant.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Restaurant not found"
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
    
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)
