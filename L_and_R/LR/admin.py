from django.contrib import admin
from django.apps import apps
from django.utils.timezone import now
from datetime import timedelta
from .models import PaymentTransaction, Subscription

# Register all models dynamically, except PaymentTransaction and Subscription (to customize them)
app_models = apps.get_app_config('LR').get_models()

for model in app_models:
    if model not in [PaymentTransaction, Subscription]:  # Exclude these to customize separately
        admin.site.register(model)

# ✅ PaymentTransaction Admin Customization
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_id", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("transaction_id", "user__app_username", "customer_email")
    ordering = ("-created_at",)
    list_editable = ("status",)
    readonly_fields = ("transaction_id", "user", "amount", "created_at")
    actions = ["mark_as_verified"]

    # ✅ Automatically activate subscription upon verification
    def save_model(self, request, obj, form, change):
        if change and obj.status == "Verified":
            # Create or update subscription
            subscription, created = Subscription.objects.get_or_create(user=obj.user)

            if float(obj.amount) == 499.0:
                subscription.subscription_type = "monthly"
                subscription.activate_subscription(30)  # Activate for 30 days
            elif float(obj.amount) == 4999.0:
                subscription.subscription_type = "yearly"
                subscription.activate_subscription(365)  # Activate for 1 year

            subscription.save()

        # Save the transaction status
        super().save_model(request, obj, form, change)

    # ✅ Custom action to verify selected transactions
    def mark_as_verified(self, request, queryset):
        """Verify selected transactions and activate subscription."""
        for transaction in queryset:
            if transaction.status == "Pending":
                transaction.status = "Verified"
                transaction.save()

                # Activate subscription
                subscription, created = Subscription.objects.get_or_create(user=transaction.user)
                if float(transaction.amount) == 499.0:
                    subscription.subscription_type = "monthly"
                    subscription.activate_subscription(30)
                elif float(transaction.amount) == 4999.0:
                    subscription.subscription_type = "yearly"
                    subscription.activate_subscription(365)

                subscription.save()

        self.message_user(request, "Selected transactions have been verified and subscriptions activated.")

    mark_as_verified.short_description = "Mark selected payments as Verified"

# ✅ Register the PaymentTransaction model with the custom admin
admin.site.register(PaymentTransaction, PaymentTransactionAdmin)

# ✅ Subscription Admin Customization
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "subscription_type", "is_active", "start_date", "end_date")
    list_filter = ("is_active", "subscription_type")
    search_fields = ("user__app_username",)
    ordering = ("-start_date",)
    list_editable = ("is_active",)
    readonly_fields = ("user", "subscription_type", "start_date", "end_date")

admin.site.register(Subscription, SubscriptionAdmin)

# ✅ Customize Admin Panel Appearance
admin.site.site_header = "MediPort Admin Panel"
admin.site.site_title = "MediPort Dashboard"
admin.site.index_title = "Welcome to MediPort Admin"
