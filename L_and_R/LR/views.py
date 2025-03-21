from sqlite3 import DatabaseError, IntegrityError

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .report import *
from .scraping import *
from django.contrib import messages
from django.conf import settings
from selenium.common.exceptions import WebDriverException
from django.http import FileResponse
import os
import io
from django.contrib.auth import get_user_model
from .models import *
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.http import JsonResponse
import json
import requests
from django.core.mail import send_mail
from .forms import ContactForm
from .forms import PaymentDetailsForm
import time
from datetime import timedelta
from django.utils.timezone import now

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
            # If the instance doesn't exist, initialize it
            cls._instance = initialize_driver()

        else:
            try:
                # Check if the current WebDriver session is still active
                cls._instance.current_url  # This will raise an exception if the session is closed
            except (WebDriverException, AttributeError):
                # If the session is stale or WebDriverException occurs, reinitialize the WebDriver
                cls.quit_instance()  # Clean up the current instance
                cls._instance = initialize_driver()  # Create a new instance

        return cls._instance

    @classmethod
    def quit_instance(cls):
        """
        Closes the WebDriver instance if it exists and sets the instance to None.
        """
        if cls._instance is not None:
            try:
                cls._instance.quit()  # Close the WebDriver session
            except WebDriverException as e:
                # Log the error (you can replace print with a proper logging mechanism)
                print(f"Error closing WebDriver: {e}")
            finally:
                cls._instance = None  # Reset the instance to None

    @classmethod
    def refresh_instance(cls):
        """
        Forcefully refreshes the WebDriver instance by quitting the current session and reinitializing.
        """
        cls.quit_instance()  # Terminate the current WebDriver session
        cls._instance = initialize_driver()  # Create a new WebDriver instance


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
                # driver = WebDriverSingleton.get_instance()
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
    # driver = WebDriverSingleton.refresh_instance()
    # Render the dashboard
    return render(request, 'LR/dashboard.html')


@login_required
def download_data(request):
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


# return HttpResponse("Invalid request method.")
@login_required
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


@login_required
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
            return render(request, 'LR/success.html', {'message': 'Site password updated successfully.'})
        except AppUser.DoesNotExist:
            return render(request, 'LR/update_site_password.html', {'error': 'App username not found.'})

    return redirect('login')


@login_required
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
        request.session['fromdate'] = fromdate
        request.session['todate'] = todate

        # print(fromdate)
        # print(todate)
        # Start WebDriver instance
        driver = WebDriverSingleton.get_instance()

        # Solve captcha and input form details
        captcha_solve(driver, captcha)

        captcha_image_path = os.path.join(settings.BASE_DIR,'L_and_R/media/captchas/captcha_image.jpg')  # Replace with the actual path to the captcha image
        if os.path.exists(captcha_image_path):
            try:
                os.remove(captcha_image_path)
                print(f"Captcha image {captcha_image_path} deleted successfully!")
            except OSError as e:
                print(f"Error deleting captcha image: {e}")
        input_case_type(driver, case_type)
        #
        # Initialize message variable
        message = f"""Scheme = {scheme}<br>
                        Case Type = {case_type}<br>
                        Record = {record}<br>
                        captcha = {captcha}<br>
                        from date = {fromdate}<br>
                        to date = {todate}"""
        try:
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
        except (ConnectionAbortedError, BrokenPipeError):
            print("Client disconnected prematurely.")
            message = "Processing was interrupted due to a client disconnection."
            return redirect('login')
        # Render the success page with the message
        return render(request, 'LR/Success.html', {'message': message})

    return HttpResponse("Invalid request method.")


def login_page(request):
    return render(request, 'LR/login.html', {'user': request.user})


#
@login_required
def form_page(request):
    return render(request, 'LR/form.html')


@login_required
def captcha_view(request):
    return render(request, 'LR/form.html')


@login_required
def update_app_password(request):
    # Your logic for updating the app password
    return render(request, 'LR/update_app_password.html')


@login_required
def update_site_password(request):
    # Your logic for updating the site password
    return render(request, 'LR/update_site_password.html')


@login_required
def download_again(request):
    return render(request, 'LR/form2.html')


@login_required
def profile(request):
    user = request.user
    print(user.first_name, user.last_name, user.app_username, user.phone_number, user.email_address)  # Debugging

    return render(request, 'LR/profile.html', {'user': user})


@login_required
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
        # input_scheme(driver, scheme)

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

@login_required
def close(request):
    def is_connected():
        """Check if the system is connected to the internet."""
        try:
            requests.get("https://www.google.com", timeout=5)  # Test connection with Google
            return True
        except (requests.ConnectionError, requests.Timeout):
            return False

    if is_connected():
        # System is connected to the internet; proceed with webdriver operations
        driver = WebDriverSingleton.get_instance()
        close_driver(driver)

    # Flush session and log out the user
    auth_logout(request)
    request.session.flush()

    # Render the logout template
    return render(request, 'LR/logout.html')


@login_required
def serve_downloaded_files(request):
    files = request.session.get('downloaded_files', [])
    if len(files) == 1:
        # Serve the single combined file
        file_path = files[0]
        if os.path.exists(file_path) and file_path.endswith('.xls'):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        else:
            return HttpResponse("File not found.", status=404)
    else:
        return HttpResponse("No files available for download.", status=404)


@login_required
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

@login_required
def claimpaid(request):
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
    return render(request, 'LR/claim_paid_report.html', {'MEDIA_URL': settings.MEDIA_URL})

@login_required
def claim_paid_data(request):
    if request.method == 'POST':
        # Get form inputs
        case_type = request.POST.get('caseType')
        scheme = request.POST.get('Scheme')
        captcha = request.POST.get('captcha')
        fromdate = request.POST.get('from_date')
        todate = request.POST.get('to_date')
        print(fromdate)
        print(todate)
        # Store scheme and date range in the session
        request.session['scheme'] = scheme
        request.session['fromdate'] = fromdate
        request.session['todate'] = todate

        print(f"Processing for Scheme: {scheme}, From Date: {fromdate}, To Date: {todate}")

        # Start WebDriver instance
        driver = WebDriverSingleton.get_instance()

        # Solve captcha and input form details
        captcha_solve(driver, captcha)

        # Remove the captcha image if it exists
        captcha_image_path = os.path.join(
            settings.BASE_DIR, 'L_and_R/media/captchas/captcha_image.jpg'
        )
        if os.path.exists(captcha_image_path):
            try:
                os.remove(captcha_image_path)
                print(f"Captcha image {captcha_image_path} deleted successfully!")
            except OSError as e:
                print(f"Error deleting captcha image: {e}")

        # Input case type into the form
        # input_case_type(driver, case_type)

        # Initialize message variable
        message = ""

        try:
            # Get date intervals based on the provided date range
            intervals = get_90_day_intervals_mis(fromdate, todate)

            # Process MIS report based on the intervals and scheme
            status = mis_report(driver, scheme, intervals, request)

            # Set appropriate message based on status
            if status == "no_records":
                message = "No records found."
            elif status == "error":
                message = "An error occurred during processing."
            else:
                message = "File loaded successfully. Please download it before proceeding."

        except (ConnectionAbortedError, BrokenPipeError):
            print("Client disconnected prematurely.")
            message = "Processing was interrupted due to a client disconnection."
            return redirect('login')

        # Render the success page with the message
        return render(request, 'LR/Success.html', {'message': message})

    return HttpResponse("Invalid request method.")


def index(request):
    return render(request, 'LR/index.html')


# @csrf_exempt
@login_required
def refresh(request):
    if request.method == 'GET':  # Or 'POST' if you're using POST
        try:
            # Initialize the WebDriver instance and perform the captcha refresh
            driver = WebDriverSingleton.get_instance()
            refresh_captcha(driver)  # Call the Selenium function to refresh the captcha

            # After refreshing, render the form page with updated captcha
            return render(request, 'LR/form.html', {'MEDIA_URL': settings.MEDIA_URL})

        except Exception as e:
            # Catch any exceptions from Selenium or other errors
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    else:
        # Return an error if the request method is not allowed
        return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)

def is_user_subscribed(user):
    """Check if the user has an active subscription."""
    return Subscription.objects.filter(user=user, is_active=True, end_date__gte=timezone.now()).exists()
@login_required
def reportdownloadform(request):
    """Render the report download form only if the user has an active subscription."""
    has_active_subscription = Subscription.objects.filter(
        user=request.user, is_active=True, end_date__gte=now()
    ).exists()
    print(f"User: {request.user}, Active Subscription: {has_active_subscription}")  # Debugging print
    return render(request, 'LR/reportdownloadform.html', {'has_active_subscription': has_active_subscription})

def check_subscription(request):
    user = request.user
    is_active = Subscription.objects.filter(user=user, is_active=True).exists()
    return JsonResponse({"is_active": is_active})
@login_required
def report_download(request):
    message = main(sample=True)
    return render(request,'LR/success_report.html', {'message': message})
@login_required
def generate_reports(request):
    """
    View to handle report generation:
    - Process the selected checkboxes dynamically.
    - Generate the reports and display success or error messages in a template.
    """
    if request.method == "POST":
        # Get the selected checkboxes
        selected_reports = request.POST.getlist("report")  # List of selected checkboxes

        if not selected_reports:
            return render(request, 'LR/success_report.html', {'message': 'No checkboxes selected!'})

        # Call the main function with the selected reports
        message = main(selected_reports=selected_reports)
        return render(request, 'LR/success_report.html', {'message': message})

    # Render the error template for invalid request methods
    return render(request, 'LR/success_report.html', {'message': 'Invalid request method!'})
@login_required
def serve_download_report(request):
    """
    Serve the combined report ZIP file to the user as a downloadable response.
    """
    # Path to the ZIP file (adjust this path based on your setup)
    reports_folder = os.path.join(os.getcwd(), "Reports")
    zip_file_path = os.path.join(reports_folder, "Combined_Files.zip")

    # Check if the file exists
    if not os.path.exists(zip_file_path):
        return HttpResponse("The requested report does not exist.", status=404)

    # Serve the file as a downloadable response
    with open(zip_file_path, 'rb') as zip_file:
        response = HttpResponse(zip_file.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_file_path)}"'
        return response

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]

            # Send email (optional)
            send_mail(
                subject=f"Contact Form Submission: {subject}",
                message=f"Name: {name}\nEmail: {email}\n\n{message}",
                from_email=email,
                recipient_list=["admin@mediport.in"],  # Replace with your admin email
                fail_silently=False,
            )

            messages.success(request, "Your message has been sent successfully!")
            return redirect("contact")  # Redirect to avoid form resubmission

    else:
        form = ContactForm()

    return render(request, "LR/contact.html", {"form": form})

@login_required
def payment_page(request):
    user = request.user  # Get the logged-in user

    # Pre-fill user details
    user_data = {
        'full_name': f"{user.first_name} {user.last_name}",
        'email': user.email_address,
        'phone': user.phone_number,
        'address': user.address
    }

    return render(request, 'LR/payment_details.html', {'user_data': user_data})  # Create this template with QR code

def submit_transaction(request):
    if request.method == "POST":
        transaction_id = request.POST.get("transaction_id")
        amount = request.POST.get("subscription")

        # Get auto-filled user details
        customer_name = request.user.first_name + " " + request.user.last_name
        customer_email = request.user.email_address
        customer_phone = request.user.phone_number

        if not transaction_id or not amount:
            messages.error(request, "Transaction ID and Amount are required!")
            return redirect("payment_page")

        # Prevent duplicate transactions
        if PaymentTransaction.objects.filter(transaction_id=transaction_id).exists():
            messages.error(request, "Transaction ID already submitted!")
            return redirect("payment_page")

        # Create a new transaction record
        PaymentTransaction.objects.create(
            user=request.user,
            transaction_id=transaction_id,
            amount=amount,
            status="Pending",
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone
        )

        # ✅ Redirect to report download form with success message
        messages.success(request, "Your request is successfully submitted. Waiting for the verification.")
        return redirect("reportdownloadform")

    return redirect("payment_page")


@staff_member_required
def verify_transaction(request, transaction_id):
    """Admin verifies a payment and activates the user's subscription."""
    try:
        transaction = PaymentTransaction.objects.get(transaction_id=transaction_id)
    except PaymentTransaction.DoesNotExist:
        messages.error(request, "Transaction not found!")
        return redirect("admin:index")  # Redirect to admin dashboard

    if transaction.status == "Pending":
        # ✅ Mark the transaction as Verified
        transaction.status = "Verified"
        transaction.save()

        # ✅ Ensure subscription exists or create one
        subscription, created = Subscription.objects.get_or_create(user=transaction.user)
        print(f"Subscription created: {created} for user: {transaction.user.app_username}")

        # ✅ Activate subscription based on payment amount
        if float(transaction.amount) == 499.0:
            subscription.subscription_type = "monthly"
            subscription.activate_subscription(30)  # Activate for 30 days
        elif float(transaction.amount) == 4999.0:
            subscription.subscription_type = "yearly"
            subscription.activate_subscription(365)  # Activate for 1 year
        else:
            messages.error(request, "Invalid subscription amount detected!")
            return redirect("admin:index")

        # ✅ Save the subscription
        subscription.save()

        # ✅ Debugging Output
        print(f"Subscription activated: {subscription.is_active} | Start: {subscription.start_date} | End: {subscription.end_date}")

        messages.success(request, f"Transaction verified and subscription activated for {transaction.user.app_username}!")
    else:
        messages.info(request, "Transaction is already verified or failed!")

    return redirect("admin:index")
@staff_member_required
def admin_dashboard(request):
    """Admin dashboard to view pending transactions."""
    transactions = PaymentTransaction.objects.filter(status="Pending")
    return render(request, "LR/admin_dashboard.html", {"transactions": transactions})
