"""Load generator output into the database.

The command is idempotent: transactions are keyed by the identifier the
generator produced, so running it twice leaves the same rows behind.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction

from apps.accounts.models import Account
from apps.transactions.models import (
    AnomalyFlag,
    Category,
    Merchant,
    Subscription,
    Transaction,
)

# Human readable names for the slugs the generator emits.
CATEGORY_NAMES = {
    "salary": ("Salary", True),
    "rent": ("Rent", False),
    "subscription": ("Subscription", False),
    "utilities": ("Utilities", False),
    "groceries": ("Groceries", False),
    "dining": ("Dining", False),
    "electronics": ("Electronics", False),
    "travel": ("Travel", False),
    "health": ("Health", False),
    "other": ("Other", False),
}

# Opening balances the generator starts each profile from.
OPENING_BALANCES = {
    "student": Decimal("4200.00"),
    "employee": Decimal("28500.00"),
    "freelancer": Decimal("41000.00"),
}


def merchant_name(raw_description: str) -> str:
    """Strip the trailing terminal number from a card description."""
    head, _, tail = raw_description.rpartition(" ")
    if head and tail.isdigit():
        return head
    return raw_description


class Command(BaseCommand):
    help = "Load a generated statement and its ground truth into the database"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--file",
            type=Path,
            required=True,
            help="path to a transactions json file produced by the generator",
        )
        parser.add_argument(
            "--labels",
            type=Path,
            help="path to the matching labels file, defaults to a sibling file",
        )
        parser.add_argument(
            "--profile",
            help="account profile, defaults to the one encoded in the file name",
        )
        parser.add_argument(
            "--account-name",
            help="name given to the account, defaults to the profile",
        )

    def handle(self, *args, **options) -> None:
        source = self._resolve(options["file"])
        labels_path = options.get("labels")
        if labels_path is None:
            labels_path = source.with_name(
                source.name.replace("transactions_", "labels_")
            )
        labels_file = self._resolve(Path(labels_path))

        transactions = self._read(source)
        labels = {item["transaction_id"]: item for item in self._read(labels_file)}

        missing = {item["id"] for item in transactions} - set(labels)
        if missing:
            raise CommandError(
                f"{len(missing)} transactions have no matching label entry"
            )

        profile, seed = self._parse_name(source, options.get("profile"))
        account_name = options.get("account_name") or f"{profile} account"

        with db_transaction.atomic():
            categories = self._ensure_categories()
            account = self._ensure_account(account_name, profile, seed)
            created, updated = self._load_transactions(
                account, transactions, labels, categories
            )
            flags = self._load_anomaly_flags(labels)
            subscriptions = self._load_subscriptions(account)

        self.stdout.write(
            self.style.SUCCESS(
                f"{account_name}: {created} created, {updated} updated, "
                f"{flags} anomaly flags, {subscriptions} subscriptions"
            )
        )

    def _resolve(self, path: Path) -> Path:
        candidates = [path]
        if not path.is_absolute():
            candidates.append(Path(settings.DATA_DIR) / path.name)
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise CommandError(f"file not found: {path}")

    def _read(self, path: Path) -> list[dict]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"{path} is not valid json: {exc}") from exc

    def _parse_name(self, path: Path, profile: str | None) -> tuple[str, int | None]:
        """Read profile and seed out of transactions_<profile>_<seed>.json."""
        parts = path.stem.split("_")
        parsed_profile = parts[1] if len(parts) > 2 else None
        seed = None
        if len(parts) > 2 and parts[-1].isdigit():
            seed = int(parts[-1])
        resolved = profile or parsed_profile
        if resolved is None:
            raise CommandError("could not work out the profile, pass --profile")
        return resolved, seed

    def _ensure_categories(self) -> dict[str, Category]:
        categories = {}
        for slug, (name, is_income) in CATEGORY_NAMES.items():
            category, _ = Category.objects.get_or_create(
                slug=slug, defaults={"name": name, "is_income": is_income}
            )
            categories[slug] = category
        return categories

    def _ensure_account(self, name: str, profile: str, seed: int | None) -> Account:
        account, _ = Account.objects.update_or_create(
            profile=profile,
            source_seed=seed,
            defaults={
                "name": name,
                "opening_balance": OPENING_BALANCES.get(profile, Decimal("0.00")),
            },
        )
        return account

    def _load_transactions(
        self,
        account: Account,
        transactions: list[dict],
        labels: dict[str, dict],
        categories: dict[str, Category],
    ) -> tuple[int, int]:
        merchants = self._ensure_merchants(transactions, labels, categories)
        created = 0
        updated = 0
        for item in transactions:
            label = labels[item["id"]]
            name = merchant_name(item["raw_description"])
            _, was_created = Transaction.objects.update_or_create(
                external_id=item["id"],
                defaults={
                    "account": account,
                    "date": item["date"],
                    "amount": Decimal(item["amount"]),
                    "direction": item["direction"],
                    "raw_description": item["raw_description"],
                    "balance": Decimal(item["balance"]),
                    "category": categories.get(label["category"]),
                    "merchant": merchants.get(name),
                    "series_key": label["series_id"],
                },
            )
            created += int(was_created)
            updated += int(not was_created)
        return created, updated

    def _ensure_merchants(
        self,
        transactions: list[dict],
        labels: dict[str, dict],
        categories: dict[str, Category],
    ) -> dict[str, Merchant]:
        wanted: dict[str, str] = {}
        for item in transactions:
            name = merchant_name(item["raw_description"])
            wanted.setdefault(name, labels[item["id"]]["category"])

        merchants = {}
        for name, category_slug in wanted.items():
            merchant, _ = Merchant.objects.get_or_create(
                name=name,
                defaults={
                    "display_name": name.title(),
                    "category": categories.get(category_slug),
                },
            )
            merchants[name] = merchant
        return merchants

    def _load_anomaly_flags(self, labels: dict[str, dict]) -> int:
        planted = [label for label in labels.values() if label["is_anomaly"]]
        known = {
            str(external_id): pk
            for external_id, pk in Transaction.objects.filter(
                external_id__in=[label["transaction_id"] for label in planted]
            ).values_list("external_id", "pk")
        }
        count = 0
        for label in planted:
            pk = known.get(label["transaction_id"])
            if pk is None:
                continue
            _, created = AnomalyFlag.objects.get_or_create(
                transaction_id=pk,
                kind=label["anomaly_kind"],
                source=AnomalyFlag.Source.GROUND_TRUTH,
                defaults={"note": "planted by the generator"},
            )
            count += int(created)
        return count

    def _load_subscriptions(self, account: Account) -> int:
        """Turn recurring subscription charges into subscription rows."""
        rows = (
            Transaction.objects.filter(
                account=account,
                category__slug="subscription",
                series_key__isnull=False,
            )
            .select_related("merchant")
            .order_by("date")
        )

        grouped: dict[tuple, list[Transaction]] = {}
        for row in rows:
            if row.merchant_id is None:
                continue
            grouped.setdefault((row.series_key, row.merchant_id), []).append(row)

        count = 0
        for (series_key, merchant_id), items in grouped.items():
            _, created = Subscription.objects.update_or_create(
                account=account,
                merchant_id=merchant_id,
                cadence=Subscription.Cadence.MONTHLY,
                defaults={
                    "series_key": series_key,
                    "amount": items[-1].amount,
                    "first_seen": items[0].date,
                    "last_seen": items[-1].date,
                    "is_active": True,
                },
            )
            count += int(created)
        return count
