"""Admin registrations for transaction models."""

from django.contrib import admin

from apps.transactions.models import (
    AnomalyFlag,
    Budget,
    Category,
    Merchant,
    Subscription,
    Transaction,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "is_income")
    list_filter = ("is_income",)
    search_fields = ("slug", "name")


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("name", "display_name", "category")
    list_filter = ("category",)
    search_fields = ("name", "display_name")
    raw_id_fields = ("category",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "raw_description",
        "amount",
        "direction",
        "category",
        "account",
    )
    list_filter = ("direction", "category", "account")
    search_fields = ("raw_description", "merchant__name")
    date_hierarchy = "date"
    ordering = ("-date",)
    raw_id_fields = ("account", "category", "merchant")
    list_select_related = ("category", "account", "merchant")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "merchant",
        "account",
        "amount",
        "cadence",
        "first_seen",
        "last_seen",
        "is_active",
    )
    list_filter = ("cadence", "is_active", "account")
    search_fields = ("merchant__name",)
    raw_id_fields = ("account", "merchant")


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("account", "category", "monthly_limit", "starts_on")
    list_filter = ("category", "account")
    search_fields = ("category__slug",)
    raw_id_fields = ("account", "category")


@admin.register(AnomalyFlag)
class AnomalyFlagAdmin(admin.ModelAdmin):
    list_display = ("transaction", "kind", "source", "score")
    list_filter = ("kind", "source")
    search_fields = ("transaction__raw_description", "note")
    raw_id_fields = ("transaction",)
