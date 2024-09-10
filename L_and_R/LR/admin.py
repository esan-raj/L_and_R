from django.contrib import admin
from django.apps import apps

# Get all models from the app
app_models = apps.get_app_config('LR').get_models()  # Replace 'LR' with your app name

# Register each model dynamically
for model in app_models:
    admin.site.register(model)

