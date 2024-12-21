from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Restaurant, Reservation
from product.models import MenuItem
from django.db.models import Q
from django.db.models import Count, Min, Max, Avg, F
from authentication.models import UserProfile

def restaurant_list(request):
    restaurants = Restaurant.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    kecamatan = request.GET.get('kecamatan', '')
    if kecamatan:
        restaurants = restaurants.filter(kecamatan=kecamatan)

    paginator = Paginator(restaurants, 12)  
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
                'category': menu.category,
                'description': menu.description,
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

def get_restaurant(request, pk):
    # API endpoint untuk detail restoran
    restaurant = get_object_or_404(Restaurant, pk=pk)
    
    # Ambil menu items untuk restoran ini
    menus = restaurant.menu_items.all()
    
    menu_list = [{
        'id': menu.id,
        'name': menu.name,
        'description': menu.description,
        'price': menu.price,
        'image': menu.image,
        'category': menu.category
    } for menu in menus]

    data = {
        'id': restaurant.id,
        'name': restaurant.name,
        'location': restaurant.location,
        'kecamatan': restaurant.kecamatan,
        'image': menus.first().image if menus else '',
        'menu_count': menus.count(),
        'min_price': menus.aggregate(Min('price'))['price__min'] or 0,
        'max_price': menus.aggregate(Max('price'))['price__max'] or 0,
        'avg_price': menus.aggregate(Avg('price'))['price__avg'] or 0,
        'menus': menu_list
    }
    
    return JsonResponse(data)

def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    
    menu_items = MenuItem.objects.filter(restaurant=restaurant)

    category = request.GET.get('category', '')
    if category:
        menu_items = menu_items.filter(category=category)

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

@login_required
def create_reservation(request, restaurant_id):
    """Create a new reservation for a specific restaurant"""
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    
    if request.method == 'POST':
        reservation_date = request.POST.get('date')
        
        try:
            if not reservation_date:
                messages.error(request, 'Tanggal reservasi harus diisi')
                return redirect('restaurant-detail', pk=restaurant_id)
            
            reservation = Reservation.objects.create(
                restaurant=restaurant,
                user=request.user,
                date=reservation_date
            )
            
            messages.success(request, f'Reservasi berhasil dibuat di {restaurant.name}')
            return redirect('user-reservations')
        
        except Exception as e:
            messages.error(request, f'Gagal membuat reservasi: {str(e)}')
            return redirect('restaurant-detail', pk=restaurant_id)
    
    return redirect('restaurant-detail', pk=restaurant_id)

@login_required
def user_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).select_related('restaurant')
    
    paginator = Paginator(reservations, 10)
    page = request.GET.get('page')
    reservations = paginator.get_page(page)
    
    context = {
        'reservations': reservations,
    }
    
    return render(request, 'user_reservations.html', context)

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
    
    try:
        reservation.delete()
        messages.success(request, 'Reservasi berhasil dibatalkan')
    except Exception as e:
        messages.error(request, f'Gagal membatalkan reservasi: {str(e)}')
    
    return redirect('user-reservations')

def show_json_reservations(request, pk):
    if pk == 0:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        user_profile = UserProfile.objects.get(user__id=pk)  # Access the User via the `user` field
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    
    reservations = Reservation.objects.filter(user=user_profile).select_related('restaurant')
    
    reservations_data = [{
        'id': reservation.id,
        'restaurant_name': reservation.restaurant.name,
        'restaurant_location': reservation.restaurant.location,
        'date': reservation.date.isoformat(),
        'created': reservation.created.isoformat(),
    } for reservation in reservations]
    
    return JsonResponse({
        'reservations': reservations_data
    })