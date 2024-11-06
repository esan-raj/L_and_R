from django.urls import path
from . import views

urlpatterns = [
    path('',views.index_report, name='index_report'),
    # path('refresh/',views.refresh, name='refresh'),
    path('login_page/', views.login_page_report, name='login_report'),
    # path('form/', views.form_page, name='form_page'),
    # path('process-input/', views.process_input, name='process_input'),
    # path('captcha_site/', views.captcha_view, name='captcha_view'),
    path('register/', views.register_report, name='register_report'),
    path('login/', views.login_view_report, name='login_report_app'),
    path('dashboard/',views.dashboard_view_report, name = 'dashboard_report'),
    path('update-app-password/', views.update_app_password_report, name='update_app_password_report'),
    path('update-site-password/', views.update_site_password_report, name='update_site_password_report'),
    path('update-site-password-process/', views.update_site_password_process, name='update_site_password_process'),
    path('update-app-password-process/', views.update_app_password_process, name='update_app_password_process'),
    # path('download/', views.download_data, name='download_data'),
    # path('download-again/',views.download_again, name='download_again'),
    # path('process/',views.process, name='process'),
    path('logout/',views.close_report, name='close_report'),
    # path('download_files/', views.serve_downloaded_files, name='serve_downloaded_files'),
    path('profile-view/', views.profile_view_report, name='profile_view_report'),
    path('profile/', views.profile_report, name='profile_report'),
    # path('claimpaid/', views.claimpaid, name='claimpaid'),
    # path('claimpaiddata/', views.claim_paid_data, name='claimpaiddata'),
    path('report_download_view/',views.report_download_view,name='report_download'),
    path('register_page/',views.register_view_report, name='register_view_report'),

]
