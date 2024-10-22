from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm
from .models import UserProfile

def register(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')
    
    form = UserRegistrationForm()
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('authentication:login')
    
    context = {"form": form}
    return render(request, "register.html", context)

def login_user(request):
    if request.user.is_authenticated:
        return redirect('main:show_main')
    
    context = {}

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_page = request.GET.get("next")
            response = redirect(next_page) if next_page else redirect("main:show_main")
            response.set_cookie("user_logged_in", user.username)
            return response
        else:
            messages.error(request, "Sorry, incorrect username or password. Please try again.")
    
    return render(request, "login.html", context)

@login_required
def logout_user(request):
    logout(request)
    response = redirect('authentication:login')
    response.delete_cookie('user_logged_in')
    messages.info(request, 'You have been logged out.')
    return response