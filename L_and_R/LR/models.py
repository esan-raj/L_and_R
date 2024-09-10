from django.db import models
from django.utils import timezone
class AppUser(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    app_username = models.CharField(max_length=50, unique=True)
    app_password = models.CharField(max_length=50)
    site_username = models.CharField(max_length=50, unique=True)
    site_password = models.CharField(max_length=50)
    organization = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email_address = models.EmailField()
    address = models.TextField()
    date_of_joining = models.DateField(default = timezone.now)
    is_active = models.BooleanField(default=True)

    objects = models.Manager()

class DynamicExcelData(models.Model):
    data = models.JSONField()  # Store the data dynamically
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.app_username


