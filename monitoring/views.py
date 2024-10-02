from .models import *
import re
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required



def home(request):
    return render(request, 'index.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = auth.authenticate(request, username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST.get('password2')  # Confirm password field
        phone_number = request.POST.get('phone_number')  # Phone number field

        if len(username) < 6:
            messages.error(
                request, "Username must be at least 6 characters long")
            return redirect('signup')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Invalid email address")
            return redirect('signup')

        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not re.match(password_pattern, password1):
            messages.error(
                request, "Password must be at least 8 characters long, include numbers, special characters, one uppercase letter, and one lowercase letter.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already taken")
            return redirect('signup')
        
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        user = User.objects.create_user(
            username=username, email=email, password=password1)
        user.save()
        messages.success(request, "User added Successfully")
        return redirect('signup')

    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('home')