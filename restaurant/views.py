# from django.shortcuts import render

# # Create your views here.
# restaurant/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Restaurant
from product.models import MenuItem
from django.db.models import Q
from django.db.models import Count, Min, Max, Avg, F
from django.views.decorators.csrf import csrf_exempt


def restaurant_list(request):
    """View untuk menampilkan daftar restoran dengan filter"""
    # Ambil semua restoran
    restaurants = Restaurant.objects.all()

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Filter berdasarkan kecamatan
    kecamatan = request.GET.get('kecamatan', '')
    if kecamatan:
        restaurants = restaurants.filter(kecamatan=kecamatan)

    # Pagination
    paginator = Paginator(restaurants, 12)  # 12 restoran per halaman
    page = request.GET.get('page')
    restaurants = paginator.get_page(page)

    context = {
        'restaurants': restaurants,
        'kecamatans': Restaurant.KECAMATAN_CHOICE,
        'search_query': search_query,
        'selected_kecamatan': kecamatan,
    }
    
    return render(request, 'restaurant_list.html', context)

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
    restaurants_data = [{
        'id': restaurant.id,
        'name': restaurant.resto_name,
        'kecamatan': restaurant.kecamatan,
        'location': restaurant.location,
        'menu_count': restaurant.menu_count,
        'min_price': restaurant.min_price,
        'max_price': restaurant.max_price,
        'image': restaurant.image,
    } for restaurant in page_obj]
    
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

def restaurant_detail(request, pk):
    """View untuk menampilkan detail restoran dan menu-menunya"""
    restaurant = get_object_or_404(Restaurant, pk=pk)
    
    # Ambil menu items untuk restoran ini
    menu_items = MenuItem.objects.filter(restaurant=restaurant)

    # Filter menu berdasarkan kategori
    category = request.GET.get('category', '')
    if category:
        menu_items = menu_items.filter(category=category)

    # Filter berdasarkan range harga
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        menu_items = menu_items.filter(price__gte=min_price)
    if max_price:
        menu_items = menu_items.filter(price__lte=max_price)

    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'categories': MenuItem.CATEGORY_CHOICES,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
    }
    
    return render(request, 'restaurant_detail.html', context)

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
    restaurants_data = [{
        'id': restaurant.id,
        'name': restaurant.resto_name,
        'kecamatan': restaurant.kecamatan,
        'location': restaurant.location,
        'menu_count': restaurant.menu_count,
        'min_price': restaurant.min_price,
        'max_price': restaurant.max_price,
        'image': restaurant.image,
    } for restaurant in page_obj]
    
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

def restaurant_detail_json(request, resto_name):
    try:
        # Get restaurant details
        restaurant = Restaurant.objects.filter(name=resto_name).first()
        
        if not restaurant:
            return JsonResponse({
                "status": "error",
                "message": "Restaurant not found"
            }, status=404)
        
        # Get menu statistics
        stats = (MenuItem.objects
                .filter(restaurant=restaurant)
                .aggregate(
                    menu_count=Count('id'),
                    min_price=Min('price'),
                    max_price=Max('price'),
                    avg_price=Avg('price')
                ))
        
        # Get all menu items and categories
        menu_items = MenuItem.objects.filter(restaurant=restaurant)
        
        # Format response data
        response_data = {
            "status": "success",
            "restaurant": {
                "name": restaurant.name,
                "kecamatan": restaurant.kecamatan,
                "location": restaurant.location
            },
            "stats": {
                "menu_count": stats['menu_count'],
                "min_price": stats['min_price'],
                "max_price": stats['max_price'],
                "avg_price": float(stats['avg_price']) if stats['avg_price'] else 0
            },
            "menu_items": [{
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "price": item.price,
                "image": item.image,
                "category": item.category
            } for item in menu_items]
        }
        
        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
    
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
