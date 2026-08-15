"""Endpoints for account models."""

from django.db.models import Count
from rest_framework import viewsets

from apps.accounts.models import Account
from apps.accounts.serializers import AccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.annotate(transaction_count=Count("transactions"))
    serializer_class = AccountSerializer
    filterset_fields = ("profile", "currency")
    search_fields = ("name",)
    ordering_fields = ("name", "created_at")
    ordering = ("name",)
