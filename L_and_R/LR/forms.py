from django import forms
from .models import AppUser, PaymentTransaction  # Keeping this for RegistrationForm

class RegistrationForm(forms.ModelForm):
    app_password_confirm = forms.CharField(max_length=50, widget=forms.PasswordInput())
    site_password_confirm = forms.CharField(max_length=50, widget=forms.PasswordInput())

    class Meta:
        model = AppUser
        fields = [
            'first_name',
            'last_name',
            'app_username',
            'password',
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
            'password': forms.PasswordInput(),
            'site_password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        site_password = cleaned_data.get("site_password")
        site_password_confirm = cleaned_data.get("site_password_confirm")

        if password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        if site_password != site_password_confirm:
            self.add_error('site_password_confirm', "Site passwords do not match.")


# New Contact Form
class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter email address"})
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter subject"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Enter your message"})
    )

class PaymentDetailsForm(forms.ModelForm):
    class Meta:
        model = PaymentTransaction
        fields = ['customer_name', 'customer_email', 'customer_phone']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your name'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            
