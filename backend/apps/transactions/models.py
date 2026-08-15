"""Transaction level models."""

from django.db import models

from apps.accounts.models import Account
from apps.common.models import TimeStampedModel


class Category(TimeStampedModel):
    """Spending category, keyed by a stable slug."""

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    is_income = models.BooleanField(default=False)

    class Meta:
        ordering = ("slug",)
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.slug


class Merchant(TimeStampedModel):
    """A counterparty recognised from the raw statement text."""

    name = models.CharField(max_length=160, unique=True)
    display_name = models.CharField(max_length=160, blank=True)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="merchants",
    )

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Transaction(TimeStampedModel):
    """A single booked movement on an account."""

    class Direction(models.TextChoices):
        IN = "in", "Incoming"
        OUT = "out", "Outgoing"

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions"
    )
    # identity coming from the generator, used to keep loading idempotent
    external_id = models.UUIDField(unique=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    direction = models.CharField(max_length=3, choices=Direction.choices)
    raw_description = models.CharField(max_length=255)
    balance = models.DecimalField(max_digits=14, decimal_places=2)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    merchant = models.ForeignKey(
        Merchant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )
    # set when the transaction belongs to a recurring series
    series_key = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ("-date", "-created_at")
        indexes = [
            models.Index(fields=["date"], name="transaction_date_idx"),
            models.Index(fields=["account"], name="transaction_account_idx"),
            models.Index(
                fields=["account", "date"], name="transaction_account_date_idx"
            ),
            models.Index(fields=["series_key"], name="transaction_series_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.date} {self.raw_description} {self.amount}"

    @property
    def signed_amount(self):
        """Amount with the sign the account holder would expect."""
        return self.amount if self.direction == self.Direction.IN else -self.amount


class Subscription(TimeStampedModel):
    """A recurring charge detected for an account."""

    class Cadence(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="subscriptions"
    )
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="subscriptions"
    )
    series_key = models.UUIDField(null=True, blank=True)
    cadence = models.CharField(
        max_length=10, choices=Cadence.choices, default=Cadence.MONTHLY
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    first_seen = models.DateField()
    last_seen = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("merchant__name",)
        constraints = [
            models.UniqueConstraint(
                fields=("account", "merchant", "cadence"),
                name="unique_subscription_per_account_merchant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.merchant} {self.amount} {self.cadence}"


class Budget(TimeStampedModel):
    """A monthly spending limit for one category."""

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="budgets"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="budgets"
    )
    monthly_limit = models.DecimalField(max_digits=14, decimal_places=2)
    starts_on = models.DateField()

    class Meta:
        ordering = ("category__slug",)
        constraints = [
            models.UniqueConstraint(
                fields=("account", "category"),
                name="unique_budget_per_account_category",
            )
        ]

    def __str__(self) -> str:
        return f"{self.category} {self.monthly_limit}"


class AnomalyFlag(TimeStampedModel):
    """Marks a transaction that stands out from the usual pattern."""

    class Kind(models.TextChoices):
        AMOUNT_SPIKE = "amount_spike", "Amount spike"
        DUPLICATE = "duplicate", "Duplicate"
        UNUSUAL_MERCHANT = "unusual_merchant", "Unusual merchant"
        OFF_SCHEDULE = "off_schedule", "Off schedule"

    class Source(models.TextChoices):
        GROUND_TRUTH = "ground_truth", "Ground truth"
        MODEL = "model", "Model"

    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="anomaly_flags"
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    source = models.CharField(
        max_length=16, choices=Source.choices, default=Source.GROUND_TRUTH
    )
    score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("transaction", "kind", "source"),
                name="unique_flag_per_transaction_kind_source",
            )
        ]

    def __str__(self) -> str:
        return f"{self.kind} on {self.transaction_id}"
