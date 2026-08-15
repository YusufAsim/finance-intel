"""Read and write endpoints for transaction models."""

from rest_framework import viewsets

from apps.transactions.filters import (
    BudgetFilter,
    MerchantFilter,
    SubscriptionFilter,
    TransactionFilter,
)
from apps.transactions.models import (
    AnomalyFlag,
    Budget,
    Category,
    Merchant,
    Subscription,
    Transaction,
)
from apps.transactions.serializers import (
    AnomalyFlagSerializer,
    BudgetSerializer,
    CategorySerializer,
    MerchantSerializer,
    SubscriptionSerializer,
    TransactionSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = ("is_income",)
    search_fields = ("slug", "name")
    ordering_fields = ("slug", "name", "created_at")
    ordering = ("slug",)


class MerchantViewSet(viewsets.ModelViewSet):
    queryset = Merchant.objects.select_related("category")
    serializer_class = MerchantSerializer
    filterset_class = MerchantFilter
    search_fields = ("name", "display_name")
    ordering_fields = ("name", "created_at")
    ordering = ("name",)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related("category", "merchant", "account")
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    search_fields = ("raw_description", "merchant__name")
    ordering_fields = ("date", "amount", "created_at")
    ordering = ("-date",)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("merchant", "account")
    serializer_class = SubscriptionSerializer
    filterset_class = SubscriptionFilter
    search_fields = ("merchant__name",)
    ordering_fields = ("amount", "first_seen", "last_seen")
    ordering = ("merchant__name",)


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related("category", "account")
    serializer_class = BudgetSerializer
    filterset_class = BudgetFilter
    search_fields = ("category__slug",)
    ordering_fields = ("monthly_limit", "starts_on")
    ordering = ("category__slug",)


class AnomalyFlagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnomalyFlag.objects.select_related("transaction")
    serializer_class = AnomalyFlagSerializer
    filterset_fields = ("kind", "source", "transaction__account")
    search_fields = ("transaction__raw_description", "note")
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)
