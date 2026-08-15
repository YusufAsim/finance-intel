"""Query filters exposed on the list endpoints."""

from django_filters import rest_framework as filters

from apps.transactions.models import Budget, Merchant, Subscription, Transaction


class TransactionFilter(filters.FilterSet):
    """Date range, amount range, category slug and account."""

    date_after = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = filters.DateFilter(field_name="date", lookup_expr="lte")
    amount_min = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = filters.NumberFilter(field_name="amount", lookup_expr="lte")
    category = filters.CharFilter(field_name="category__slug")
    merchant = filters.CharFilter(field_name="merchant__name", lookup_expr="icontains")

    class Meta:
        model = Transaction
        fields = (
            "account",
            "direction",
            "category",
            "merchant",
            "date_after",
            "date_before",
            "amount_min",
            "amount_max",
        )


class SubscriptionFilter(filters.FilterSet):
    merchant = filters.CharFilter(field_name="merchant__name", lookup_expr="icontains")

    class Meta:
        model = Subscription
        fields = ("account", "cadence", "is_active", "merchant")


class BudgetFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__slug")

    class Meta:
        model = Budget
        fields = ("account", "category")


class MerchantFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__slug")

    class Meta:
        model = Merchant
        fields = ("category",)
