"""
URL configuration for southfeast project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('auth/', include ('authentication.urls')),
    path('product/', include('product.urls')),
    path('menu/', include('product.urls')),
    path('restaurant/', include('restaurant.urls')),
    path('review/', include('review.urls')),
    path('wishlist/', include('wishlist.urls')),
    path('forum/', include('forum.urls')),
<<<<<<< HEAD
<<<<<<< HEAD
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
    path('dashboard/', include('dashboard.urls')),
]
>>>>>>> 69004f5daaaa2b72bbc0ca83b4739df8968c818e


=======
    path('dashboard/', include('dashboard.urls')),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> f453a6ce70aa1a086973e2e372dddfaff10d8a0d
