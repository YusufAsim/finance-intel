"""Remove every domain row, leaving auth and admin tables alone."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction

from apps.accounts.models import Account
from apps.transactions.models import (
    AnomalyFlag,
    Budget,
    Category,
    Merchant,
    Subscription,
    Transaction,
)

# Deleted in this order so foreign keys never block a step.
DELETION_ORDER = (
    AnomalyFlag,
    Budget,
    Subscription,
    Transaction,
    Merchant,
    Category,
    Account,
)


class Command(BaseCommand):
    help = "Delete all accounts, transactions and everything hanging off them"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--yes",
            action="store_true",
            help="confirm the deletion, required because this cannot be undone",
        )

    def handle(self, *args, **options) -> None:
        if not options["yes"]:
            raise CommandError("refusing to delete anything without --yes")

        with db_transaction.atomic():
            for model in DELETION_ORDER:
                deleted, _ = model.objects.all().delete()
                self.stdout.write(f"{model.__name__}: {deleted} deleted")

        self.stdout.write(self.style.SUCCESS("domain tables are empty"))
