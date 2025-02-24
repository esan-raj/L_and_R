from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta

# Custom manager for AppUser
class AppUserManager(BaseUserManager):
    def create_user(self, app_username, password=None, **extra_fields):
        if not app_username:
            raise ValueError('The App Username must be set')
        app_username = self.normalize_email(app_username)
        user = self.model(app_username=app_username, **extra_fields)
        user.set_password(password)  # Hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, app_username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(app_username, password, **extra_fields)

# Custom user model
class AppUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50, null = True)
    last_name = models.CharField(max_length=50, null = True)
    app_username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=50, default='default_password')# For login to your website
    site_username = models.CharField(max_length=50, unique=True)  # For login to the scraped website
    site_password = models.CharField(max_length=128, null = True)  # Store hashed site password if necessary
    organization = models.CharField(max_length=100, null = True)
    phone_number = models.CharField(max_length=10, null = True)
    email_address = models.EmailField()
    address = models.TextField()
    date_of_joining = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Required for admin access

    USERNAME_FIELD = 'app_username'  # Use app_username as the primary login field
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email_address']

    objects = AppUserManager()

    def __str__(self):
        return self.app_username

    @property
    def is_authenticated(self):
        return True



class DynamicExcelData(models.Model):
    data = models.JSONField()  # Store the data dynamically
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.uploaded_at)

# Add new payment-related models below

class PaymentTransaction(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True)
    order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Remove this line if `currency` already exists
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Verified', 'Verified'), ('Failed', 'Failed')],
        default='Pending'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ Add this field safely
    payment_details = models.TextField(null=True, blank=True)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_email = models.EmailField(null=True, blank=True)
    customer_phone = models.CharField(max_length=15, null=True, blank=True)


    def __str__(self):
        return f"{self.user.app_username} - {self.transaction_id} - {self.status}"




class Subscription(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    subscription_type = models.CharField(
        max_length=20,
        choices=[("monthly", "Monthly"), ("yearly", "Yearly")],
        default="monthly"
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def activate_subscription(self, duration_days):
        """Activate subscription for a given duration (e.g., 30 days for monthly)."""
        self.is_active = True
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=duration_days)
        self.save()

    def __str__(self):
        return f"{self.user.app_username} - {self.subscription_type} - {'Active' if self.is_active else 'Inactive'}"


class ReportDownloadLog(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    report_name = models.CharField(max_length=255)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.app_username} - {self.report_name} - {self.downloaded_at}"

