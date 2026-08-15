"""Serializers for account models."""

from rest_framework import serializers

from apps.accounts.models import Account


class AccountSerializer(serializers.ModelSerializer):
    transaction_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Account
        fields = (
            "id",
            "name",
            "profile",
            "currency",
            "opening_balance",
            "source_seed",
            "transaction_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
