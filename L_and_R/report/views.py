import zipfile
from django.utils import timezone
from sqlite3 import DatabaseError, IntegrityError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

# from .scraping import *
from django.contrib import messages
from django.conf import settings
from selenium.common.exceptions import WebDriverException
from django.http import FileResponse
import os
import io
from django.contrib.auth import get_user_model
# from .models import AppUser
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
AppUser = get_user_model()
# Create your views here.
def index_report (request):
    return render(request,'report/index.html')

def login_view_report(request):
    if request.method == 'POST':
        app_username = request.POST.get('app_username')
        app_password = request.POST.get('app_password')

        # Authenticate using your custom user model
        try:
            # Attempt to retrieve the user from the database
            user = AppUser.objects.get(app_username=app_username)

            # Check if the provided password matches
            if check_password(app_password, user.password):
                login(request, user)  # Login the user with Django's login method

                # Store additional user info in the session if needed
                request.session['user_id'] = user.id
                request.session['app_username'] = app_username
                # driver = WebDriverSingleton.get_instance()
                # Redirect to the dashboard page
                return redirect('dashboard_report')
            else:
                # Password mismatch
                return render(request, 'report/login.html', {'error': 'Invalid username or password'})

        except AppUser.DoesNotExist:
            # Username not found in the database
            return render(request, 'report/login.html', {'error': 'Invalid username or password'})

    # Render the login page for GET requests
    return render(request, 'report/login.html')

def register_report(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        app_username = request.POST.get('app_username')
        password = request.POST.get('app_password')
        password_confirm = request.POST.get('app_password_confirm')
        site_username = request.POST.get('site_username')
        site_password = request.POST.get('site_password')
        site_password_confirm = request.POST.get('site_password_confirm')
        phone_number = request.POST.get('phone_number')
        email_address = request.POST.get('email_address')
        organization = request.POST.get('organization')
        address = request.POST.get('address')
        doj = request.POST.get('doj')

        # Password matching checks
        if password != password_confirm:
            messages.error(request, "App passwords do not match.")
            password = ''
            password_confirm = ''

        if site_password != site_password_confirm:
            messages.error(request, "Site passwords do not match.")
            site_password = ''
            site_password_confirm = ''

        if AppUser.objects.filter(site_username=site_username).exists():
            messages.error(request, 'The site username is already taken. Please choose another one.')
            return render(request, 'report/register.html')

            # Check if app_username already exists
        if AppUser.objects.filter(app_username=app_username).exists():
            messages.error(request, 'The app username is already taken. Please choose another one.')
            return render(request, 'report/register.html')

        # Save user details even if passwords do not match
        user = AppUser(
            first_name=first_name,
            last_name=last_name,
            app_username=app_username,
            site_username=site_username,
            site_password=site_password,
            phone_number=phone_number,
            email_address=email_address,
            organization=organization,
            address=address,
            date_of_joining=doj
        )

        # Hash passwords before saving
        if password:
            user.set_password(password)  # Hashes the app password
        # if site_password:
        #     user.site_password = make_password(site_password)  # Hashes the site password

        user.save()

        messages.success(request, "Your account has been created successfully.")
        return redirect('login')

    return render(request, 'report/register.html')

def login_page_report(request):
    return render(request, 'report/login.html',{'user': request.user})

def profile_report(request):
    user = request.user
    print(user.first_name, user.last_name, user.app_username, user.phone_number, user.email_address)  # Debugging

    return render(request, 'LR/profile.html', {'user': user})

def close_report(request):
    auth_logout(request)
    request.session.flush()
    return render(request,'report/logout.html')

def profile_view_report(request):
    user = request.user
    print(user.first_name, user.last_name, user.app_username, user.phone_number, user.email_address)
    if request.method == 'POST':
        # Fetch updated values from the form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        app_username = request.POST.get('app_username')
        phone_number = request.POST.get('phone_number')
        email_address = request.POST.get('email_address')

        try:
            # Update user profile details
            user.first_name = first_name
            user.last_name = last_name
            user.app_username = app_username
            user.phone_number = phone_number
            user.email = email_address

            # Attempt to save the updated user object
            user.save()

            # Add a success message and redirect to the dashboard
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('dashboard')

        except IntegrityError:
            # This handles database-related errors like uniqueness violations (e.g., duplicate username)
            messages.error(request, 'A database error occurred. Please ensure the username or email is unique.')

        except ValidationError as e:
            # This handles validation-related errors, such as invalid field data
            messages.error(request, f'Invalid data: {e.message}')

        except Exception as e:
            # General exception handler for any unexpected errors
            messages.error(request, f'An unexpected error occurred: {e}')

    # If it's a GET request, just render the profile form with current user data
    return render(request, 'report/profile.html', {'user': user})

def dashboard_view_report(request):
    app_username = request.session.get('app_username')
    if not app_username:
        return redirect('login_report')
    # Render the dashboard
    return render(request, 'report/dashboard.html')

def update_app_password_process(request):
    if request.method == 'POST':
        app_username = request.session.get('app_username')  # Fetch from session
        new_app_password = request.POST.get('new_app_password')

        try:
            user = AppUser.objects.get(app_username=app_username)
            user.set_password(new_app_password)  # Hash the new password
            user.save()
            messages.success(request, 'App password updated successfully.')
            return render(request, 'report/login.html')
        except AppUser.DoesNotExist:
            messages.error(request, 'App username not found.')
            return render(request, 'report/update_app_password.html', {'error': 'App username not found.'})

    return redirect('login_report')


def update_site_password_process(request):
    if request.method == 'POST':
        app_username = request.session.get('app_username')  # Fetch from session
        print(app_username)
        new_site_password = request.POST.get('new_site_password')

        try:
            user = AppUser.objects.get(app_username=app_username)
            # Hash the new site password before saving
            user.site_password = new_site_password
            user.save()
            return render(request, 'report/success.html', {'message': 'Site password updated successfully.'})
        except AppUser.DoesNotExist:
            return render(request, 'report/update_site_password.html', {'error': 'App username not found.'})

    return redirect('login_report')

def update_app_password_report(request):
    # Your logic for updating the app password
    return render(request, 'report/update_app_password.html')

def update_site_password_report(request):
    # Your logic for updating the site password
    return render(request, 'report/update_site_password.html')

def report_download_view(request):
    return render(request,'report/reportdownloadform.html')

def register_view_report(request):
    return render(request,'report/register.html')