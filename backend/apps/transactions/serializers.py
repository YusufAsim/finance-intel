"""Serializers for transaction models."""

from rest_framework import serializers

from apps.transactions.models import (
    AnomalyFlag,
    Budget,
    Category,
    Merchant,
    Subscription,
    Transaction,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "slug", "name", "is_income", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class MerchantSerializer(serializers.ModelSerializer):
    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug", read_only=True
    )

    class Meta:
        model = Merchant
        fields = (
            "id",
            "name",
            "display_name",
            "category",
            "category_slug",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TransactionSerializer(serializers.ModelSerializer):
    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug", read_only=True
    )
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)
    signed_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "external_id",
            "account",
            "date",
            "amount",
            "signed_amount",
            "direction",
            "raw_description",
            "balance",
            "category",
            "category_slug",
            "merchant",
            "merchant_name",
            "series_key",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class SubscriptionSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(source="merchant.name", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "account",
            "merchant",
            "merchant_name",
            "series_key",
            "cadence",
            "amount",
            "first_seen",
            "last_seen",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class BudgetSerializer(serializers.ModelSerializer):
    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug", read_only=True
    )

    class Meta:
        model = Budget
        fields = (
            "id",
            "account",
            "category",
            "category_slug",
            "monthly_limit",
            "starts_on",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AnomalyFlagSerializer(serializers.ModelSerializer):
    transaction_date = serializers.DateField(source="transaction.date", read_only=True)
    transaction_amount = serializers.DecimalField(
        source="transaction.amount", max_digits=14, decimal_places=2, read_only=True
    )
    raw_description = serializers.CharField(
        source="transaction.raw_description", read_only=True
    )

    class Meta:
        model = AnomalyFlag
        fields = (
            "id",
            "transaction",
            "transaction_date",
            "transaction_amount",
            "raw_description",
            "kind",
            "source",
            "score",
            "note",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
