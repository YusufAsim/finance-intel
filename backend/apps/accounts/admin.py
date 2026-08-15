"""Admin registrations for account models."""

from django.contrib import admin

from apps.accounts.models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "profile", "currency", "opening_balance", "source_seed")
    list_filter = ("profile", "currency")
    search_fields = ("name",)
    ordering = ("name",)
