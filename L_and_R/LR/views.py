import zipfile
from django.utils import timezone
from sqlite3 import DatabaseError, IntegrityError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .scraping import *
from django.contrib import messages
from django.conf import settings
from selenium.common.exceptions import WebDriverException
from django.http import FileResponse
import os
import io
from django.contrib.auth import get_user_model
from .models import AppUser
from django.contrib.auth import authenticate, login

AppUser = get_user_model()
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
            return render(request, 'LR/register.html')

            # Check if app_username already exists
        if AppUser.objects.filter(app_username=app_username).exists():
            messages.error(request, 'The app username is already taken. Please choose another one.')
            return render(request, 'LR/register.html')

        # Save user details even if passwords do not match
        user = AppUser(
            first_name=first_name,
            last_name=last_name,
            app_username=app_username,
            site_username=site_username,
            phone_number=phone_number,
            email_address=email_address,
            organization=organization,
            address=address,
            date_of_joining=timezone.now()
        )

        # Hash passwords before saving
        if password:
            user.set_password(password)  # Hashes the app password
        if site_password:
            user.site_password = make_password(site_password)  # Hashes the site password

        user.save()

        messages.success(request, "Your account has been created successfully.")
        return redirect('login')

    return render(request, 'LR/register.html')


# @login_required
def login_view(request):
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
                driver = WebDriverSingleton.get_instance()
                # Redirect to the dashboard page
                return redirect('dashboard')
            else:
                # Password mismatch
                return render(request, 'LR/login.html', {'error': 'Invalid username or password'})

        except AppUser.DoesNotExist:
            # Username not found in the database
            return render(request, 'LR/login.html', {'error': 'Invalid username or password'})

    # Render the login page for GET requests
    return render(request, 'LR/login.html')
@login_required
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
        new_app_password = request.POST.get('new_app_password')

        try:
            user = AppUser.objects.get(app_username=app_username)
            user.set_password(new_app_password)  # Hash the new password
            user.save()
            messages.success(request, 'App password updated successfully.')
            return render(request, 'LR/login.html')
        except AppUser.DoesNotExist:
            messages.error(request, 'App username not found.')
            return render(request, 'LR/update_app_password.html', {'error': 'App username not found.'})

    return redirect('login')


def update_site_password_process(request):
    if request.method == 'POST':
        app_username = request.session.get('app_username')  # Fetch from session
        print(app_username)
        new_site_password = request.POST.get('new_site_password')

        try:
            user = AppUser.objects.get(app_username=app_username)
            # Hash the new site password before saving
            user.site_password = make_password(new_site_password)
            user.save()
            return render(request, 'LR/success.html', {'message': 'Site password updated successfully.'})
        except AppUser.DoesNotExist:
            return render(request, 'LR/update_site_password.html', {'error': 'App username not found.'})

    return redirect('login')


def process_input(request):
    if request.method == 'POST':
        # Get form inputs
        case_type = request.POST.get('caseType')
        scheme = request.POST.get('Scheme')
        record = request.POST.get('recordPeriod')
        captcha = request.POST.get('captchaInput')
        fromdate = request.POST.get('advFromDate')
        todate = request.POST.get('advToDate')
        request.session['scheme'] = scheme
        print(fromdate)
        print(todate)
        # Start WebDriver instance
        driver = WebDriverSingleton.get_instance()

        # Solve captcha and input form details
        captcha_solve(driver, captcha)
        input_case_type(driver, case_type)
        input_scheme(driver, scheme)



        # Initialize message variable
        message = ""

        if record:  # If recordPeriod is filled, download with record
            print("Record period found, downloading with record.")
            status = download_excel(driver, scheme, record)
        else:  # If recordPeriod is not filled, download with selected_option
            print("Record period not found, processing dropdown options.")
            # Get the intervals based on fromdate and todate
            intervals = get_90_day_intervals(fromdate, todate)
            # Assuming process_dates_and_download handles dropdown options
            status = process_dates_and_download(driver, intervals, scheme, request)

            # For simplicity, assuming this function handles the download_excel internally
            # and processes the selected_option.

            # Set message based on the status (if available from process_dates_and_download)
              # Assuming this is set based on the process

        # Handle status messages based on download_excel results
        if status == "no_records":
            message = "No records found."
        elif status == "error":
            message = "An error occurred during processing."
        else:
            message = "File loaded successfully. Please download it before moving ahead"

        # Render the success page with the message
        return render(request, 'LR/Success.html', {'message': message})

    return HttpResponse("Invalid request method.")


def login_page(request):
    return render(request, 'LR/login.html',{'user': request.user})
#
#
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

def profile(request):
    user = request.user
    print(user.first_name, user.last_name, user.app_username, user.phone_number, user.email_address)  # Debugging

    return render(request, 'LR/profile.html', {'user': user})

def process(request):
    if request.method == 'POST':
        # Get form inputs
        case_type = request.POST.get('caseType')
        scheme = request.POST.get('Scheme')
        record = request.POST.get('recordPeriod')
        # captcha = request.POST.get('captchaInput')
        fromdate = request.POST.get('advFromDate')
        todate = request.POST.get('advToDate')
        request.session['scheme'] = scheme
        request.session['fromdate'] = fromdate
        request.session['todate'] = todate
        print(fromdate)
        print(todate)
        # Start WebDriver instance
        driver = WebDriverSingleton.get_instance()

        # Solve captcha and input form details
        # captcha_solve(driver, captcha)
        input_case_type(driver, case_type)
        input_scheme(driver, scheme)

        # Initialize message variable
        message = ""

        if record:  # If recordPeriod is filled, download with record
            print("Record period found, downloading with record.")
            status = download_excel(driver, scheme, record)
        else:  # If recordPeriod is not filled, download with selected_option
            print("Record period not found, processing dropdown options.")
            # Get the intervals based on fromdate and todate
            intervals = get_90_day_intervals(fromdate, todate)
            # Assuming process_dates_and_download handles dropdown options
            status = process_dates_and_download(driver, intervals, scheme, request)

            # For simplicity, assuming this function handles the download_excel internally
            # and processes the selected_option.

            # Set message based on the status (if available from process_dates_and_download)
            # Assuming this is set based on the process

        # Handle status messages based on download_excel results
        if status == "no_records":
            message = "No records found."
        elif status == "error":
            message = "An error occurred during processing."
        else:
            message = "File loaded successfully. Please download it before moving ahead"

        # Render the success page with the message
        return render(request, 'LR/Success.html', {'message': message})

    return HttpResponse("Invalid request method.")

def close(request):
    driver = WebDriverSingleton.get_instance()
    close_driver(driver)
    return render(request,'LR/logout.html')


def serve_downloaded_files(request):
    files = request.session.get('downloaded_files', [])
    scheme = request.session.get('scheme')
    fromdate = request.session.get('fromdate')
    todate = request.session.get('todate')
    if len(files) == 1:
        # Serve a single file
        file_path = files[0]
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        else:
            return HttpResponse("File not found.", status=404)

    elif len(files) > 1:
        # Create a ZIP file in memory to serve multiple files
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file_path in files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))  # Add the file to the zip archive

        zip_buffer.seek(0)  # Set the pointer to the beginning of the file

        response = FileResponse(zip_buffer, as_attachment=True, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{scheme}_files_from_{fromdate}_to_{todate}.zip"'
        return response
    else:
        return HttpResponse("No files available for download.", status=404)

# @login_required
def profile_view(request):
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
    return render(request, 'LR/profile.html', {'user': user})

