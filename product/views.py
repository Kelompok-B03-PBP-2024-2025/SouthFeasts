from django.views.generic import ListView, DetailView
from django.db.models import Q, Avg
from .models import Restaurant, MenuItem
from django.shortcuts import render
from django.core.paginator import Paginator

class RestaurantListView(ListView):
    model = Restaurant
    template_name = 'product/restaurant_list.html'
    context_object_name = 'restaurants'
    paginate_by = 12

    def get_queryset(self):
        queryset = Restaurant.objects.all()
        search_query = self.request.GET.get('search', '')
        kecamatan = self.request.GET.get('kecamatan', '')
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        if kecamatan:
            queryset = queryset.filter(kecamatan=kecamatan)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kecamatans'] = Restaurant.objects.values_list('kecamatan', flat=True).distinct()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_kecamatan'] = self.request.GET.get('kecamatan', '')
        return context

class RestaurantDetailView(DetailView):
    model = Restaurant
    template_name = 'product/restaurant_detail.html'
    context_object_name = 'restaurant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get menu items for this restaurant
        context['menu_items'] = self.object.menu_items.all()
        return context

class MenuCatalogView(ListView):
    model = MenuItem
    template_name = 'product/menu_catalog.html'
    context_object_name = 'menu_items'
    paginate_by = 12

    def get_queryset(self):
        queryset = MenuItem.objects.all().select_related('restaurant')
        
        # Apply filters
        category = self.request.GET.get('category')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        kecamatan = self.request.GET.get('kecamatan')
        search_query = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category=category)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        if kecamatan:
            queryset = queryset.filter(restaurant__kecamatan=kecamatan)
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(restaurant__name__icontains=search_query)
            )
            
        # Sort options
        sort = self.request.GET.get('sort')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MenuItem.CATEGORY_CHOICES
        context['kecamatans'] = Restaurant.objects.values_list('kecamatan', flat=True).distinct()
        
        # Add filter values to context
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_kecamatan'] = self.request.GET.get('kecamatan', '')
        context['min_price'] = self.request.GET.get('min_price', '')
        context['max_price'] = self.request.GET.get('max_price', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_sort'] = self.request.GET.get('sort', '')
        
        return context