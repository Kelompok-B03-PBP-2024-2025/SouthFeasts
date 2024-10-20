from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import transaction
from .models import Profile
from .forms import CustomAuthenticationForm, UserRegistrationForm, ProfileForm

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.username = user.username
                profile.save()
            messages.success(request, f"Akun berhasil dibuat untuk {user.username}.")
            return redirect('authentication:login')  # Redirect to login page after successful registration
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileForm()
    return render(request, 'register.html', {'user_form': user_form, 'profile_form': profile_form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Anda telah berhasil masuk sebagai {username}.")
                return redirect('home')  # Ganti 'home' dengan nama URL halaman utama Anda
            else:
                messages.error(request, "Username atau password tidak valid.")
        else:
            messages.error(request, "Username atau password tidak valid.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})