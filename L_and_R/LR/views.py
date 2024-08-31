from sqlite3 import DatabaseError

from django.contrib.sessions.backends.base import UpdateError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import RegistrationForm
from .models import AppUser
from .scraping import *
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from django.contrib.sessions.exceptions import SessionInterrupted
from django.db import transaction
from django.contrib.sessions.models import Session
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException





# Singleton pattern for WebDriver
class WebDriverSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        """
        Returns a singleton instance of the WebDriver.
        Reinitializes the WebDriver if the session is stale or has been closed.
        """
        if cls._instance is None:
            cls._instance = initialize_driver()
        else:
            try:
                # Check if the current WebDriver session is still active
                cls._instance.current_url
            except (WebDriverException, AttributeError):
                # If the session is stale or WebDriverException occurs, reinitialize the WebDriver
                cls.quit_instance()
                cls._instance = initialize_driver()
        return cls._instance

    @classmethod
    def quit_instance(cls):
        """
        Closes the WebDriver instance if it exists and sets the instance to None.
        Handles any exceptions that occur during the shutdown.
        """
        if cls._instance is not None:
            try:
                close_driver(cls._instance)
            except WebDriverException as e:
                print(f"Error closing WebDriver: {e}")
            finally:
                cls._instance = None


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'LR/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        app_username = request.POST.get('app_username')
        app_password = request.POST.get('app_password')

        try:
            # Attempt to retrieve the user from the database
            user = AppUser.objects.get(app_username=app_username)

            # Check if the password matches
            if user.app_password == app_password:
                # Store user information in the session
                request.session['app_username'] = app_username
                request.session['user_id'] = user.id
                driver = WebDriverSingleton.get_instance()
                # Redirect to the dashboard page
                return redirect('dashboard')
            else:
                # If the password doesn't match, show an error message
                return render(request, 'LR/login.html', {'error': 'Invalid username or password'})

        except AppUser.DoesNotExist:
            # If the username does not exist in the database, redirect to the registration page
            return redirect('register')

    # If it's a GET request, simply render the login page
    return render(request, 'LR/login.html')

def dashboard_view(request):
    app_username = request.session.get('app_username')
    if not app_username:
        return redirect('login')

    # Render the dashboard
    return render(request, 'LR/dashboard.html')

def download_data(request):
    if request.method == 'POST':
        app_username = request.session.get('app_username')

        if not app_username:
            return redirect('login')

        # Fetch the site credentials using the app_username
        site_username = fetch_site_username(app_username)
        site_password = fetch_site_password(app_username)

        if not site_username or not site_password:
            return HttpResponse("Site credentials not found or invalid.")

        driver = WebDriverSingleton.get_instance()
        # Start the WebDriver process
        login_site(driver, site_username, site_password)

        # After processing, render form.html
        return render(request, 'LR/form.html', {'MEDIA_URL': settings.MEDIA_URL})

    return HttpResponse("Invalid request method.")

def update_app_password_process(request):
    if request.method == 'POST':
        app_username = request.session.get('app_username')  # Fetch from session
        print(app_username)
        new_app_password = request.POST.get('new_app_password')

        try:
            user = AppUser.objects.get(app_username=app_username)
            user.app_password = new_app_password
            user.save()
            return render(request, 'LR/login.html', {'message': 'App password updated successfully.'})
        except AppUser.DoesNotExist:
            return render(request, 'LR/update_app_password.html', {'error': 'App username not found.'})

    return redirect('login')


def update_site_password_process(request):
    if request.method == 'POST':
        app_username = request.session.get('app_username')  # Fetch from session
        print(app_username)
        new_site_password = request.POST.get('new_site_password')

        try:
            user = AppUser.objects.get(app_username=app_username)
            user.site_password = new_site_password
            user.save()
            return render(request, 'LR/success.html', {'message': 'Site password updated successfully.'})
        except AppUser.DoesNotExist:
            return render(request, 'LR/update_site_password.html', {'error': 'Site username not found.'})

    return redirect('login')


def process_input(request):
    if request.method == 'POST':
        case_type = request.POST.get('caseType')
        scheme = request.POST.get('Scheme')
        record = request.POST.get('recordPeriod')
        captcha = request.POST.get('captchaInput')
        driver = WebDriverSingleton.get_instance()
        captcha_solve(driver, captcha)
        input_case_type(driver, case_type)
        input_scheme(driver, scheme)
        input_period(driver, record)
        status = download_excel(driver, scheme)
        # close_driver(driver)

        if status == "no_records":
            message = "No records found."
        elif status == "error":
            message = "An error occurred during processing."
        else:
            message = "File downloaded successfully."

        return render(request, 'LR/Success.html', {'message': message})

    return HttpResponse("Invalid request method.")

def login_page(request):
    return render(request, 'LR/login.html')


def form_page(request):
    return render(request, 'LR/form.html')

def captcha_view(request):
    return render(request,'LR/form.html')

def update_app_password(request):
    # Your logic for updating the app password
    return render(request, 'LR/update_app_password.html')

def update_site_password(request):
    # Your logic for updating the site password
    return render(request, 'LR/update_site_password.html')

def download_again(request):
    return render(request,'LR/form2.html')

def process(request):
    if request.method == 'POST':
        case_type = request.POST.get('caseType')
        scheme = request.POST.get('Scheme')
        record = request.POST.get('recordPeriod')
        # captcha = request.POST.get('captchaInput')
        driver = WebDriverSingleton.get_instance()
        # captcha_solve(driver, captcha)
        input_case_type_again(driver, case_type)
        input_scheme(driver, scheme)
        input_period(driver, record)
        status = download_excel(driver, scheme)
        if status == "no_records":
            message = "No records found."
        elif status == "error":
            message = "An error occurred during processing."
        else:
            message = "File downloaded successfully."

        return render(request, 'LR/Success.html', {'message': message})

def close(request):
    driver = WebDriverSingleton.get_instance()
    close_driver(driver)
    return render(request,'LR/logout.html')

