from django import forms
from .models import AppUser

class RegistrationForm(forms.ModelForm):
    app_password_confirm = forms.CharField(max_length=50, widget=forms.PasswordInput())
    site_password_confirm = forms.CharField(max_length=50, widget=forms.PasswordInput())

    class Meta:
        model = AppUser
        fields = [
            'first_name',
            'last_name',
            'app_username',
            'app_password',
            'site_username',
            'site_password',
            'organization',
            'phone_number',
            'email_address',
            'address',
            'date_of_joining',
            'is_active',
        ]
        widgets = {
            'app_password': forms.PasswordInput(),
            'site_password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        app_password = cleaned_data.get("app_password")
        app_password_confirm = cleaned_data.get("app_password_confirm")
        site_password = cleaned_data.get("site_password")
        site_password_confirm = cleaned_data.get("site_password_confirm")

        if app_password != app_password_confirm:
            self.add_error('app_password_confirm', "App passwords do not match.")
        if site_password != site_password_confirm:
            self.add_error('site_password_confirm', "Site passwords do not match.")
