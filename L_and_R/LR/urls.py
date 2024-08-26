from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),  # Default route
    path('form/', views.form_page, name='form_page'),
    path('process/', views.process_input, name='process_input'),
    path('captcha_site/', views.captcha_view, name='captcha_view'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/',views.dashboard_view, name = 'dashboard'),
    path('update-app-password/', views.update_app_password, name='update_app_password'),
    path('update-site-password/', views.update_site_password, name='update_site_password'),
    path('update-site-password-process/', views.update_site_password_process, name='update_site_password_process'),
    path('update-app-password-process/', views.update_app_password_process, name='update_app_password_process'),
    path('download/', views.download_data, name='download_data'),
]
