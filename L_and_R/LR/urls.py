from django.urls import path
from . import views

urlpatterns = [
    path('',views.index, name='index'),
    path('refresh/',views.refresh, name='refresh'),
    path('login_page', views.login_page, name='login'),
    path('form/', views.form_page, name='form_page'),
    path('process-input/', views.process_input, name='process_input'),
    path('captcha_site/', views.captcha_view, name='captcha_view'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('dashboard/',views.dashboard_view, name = 'dashboard'),
    path('update-app-password/', views.update_app_password, name='update_app_password'),
    path('update-site-password/', views.update_site_password, name='update_site_password'),
    path('update-site-password-process/', views.update_site_password_process, name='update_site_password_process'),
    path('update-app-password-process/', views.update_app_password_process, name='update_app_password_process'),
    path('download/', views.download_data, name='download_data'),
    path('download-again/',views.download_again, name='download_again'),
    path('process/',views.process, name='process'),
    path('logout/',views.close, name='close'),
    path('download_files/', views.serve_downloaded_files, name='serve_downloaded_files'),
    path('profile-view/', views.profile_view, name='profile_view'),
    path('profile/', views.profile, name='profile'),
    path('claimpaid/', views.claimpaid, name='claimpaid'),
    path('claimpaiddata/', views.claim_paid_data, name='claimpaiddata'),
    path('reportdownloadform/', views.reportdownloadform, name='reportdownloadform'),
    path('report-download/', views.report_download, name='reportdownload'),
    path('generate-reports/', views.generate_reports, name='generate_reports'),
    path('serve-report/', views.serve_download_report, name='serve_download_report'),
    path("contact/", views.contact_view, name="contact"),
    path("payment/", views.payment_page, name="payment_page"),
    path("submit_transaction/", views.submit_transaction, name="submit_transaction"),
    path("verify_transaction/<str:transaction_id>/", views.verify_transaction, name="verify_transaction"),
    path("check-subscription/",views.check_subscription, name="check_subscription"),
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),

]

# Add this print statement to debug URL patterns
# print("URL Patterns loaded:", urlpatterns)
