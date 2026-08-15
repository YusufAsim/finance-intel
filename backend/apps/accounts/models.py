"""Account level models."""

from django.db import models

from apps.common.models import TimeStampedModel


class Account(TimeStampedModel):
    """One bank account, the root every transaction hangs off."""

    class Profile(models.TextChoices):
        STUDENT = "student", "Student"
        EMPLOYEE = "employee", "Employee"
        FREELANCER = "freelancer", "Freelancer"

    name = models.CharField(max_length=120)
    profile = models.CharField(
        max_length=20, choices=Profile.choices, default=Profile.EMPLOYEE
    )
    currency = models.CharField(max_length=3, default="TRY")
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # seed the statement was generated with, kept so a load can be repeated
    source_seed = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("profile", "source_seed"),
                name="unique_account_per_profile_and_seed",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.profile})"
