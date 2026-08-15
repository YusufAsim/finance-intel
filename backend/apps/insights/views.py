"""Account level insight endpoints.

Aggregates are computed in the database. Anything that needs a model
prediction is delegated to the ml service over http.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Account
from apps.insights.clients import MlClient, MlServiceError
from apps.insights.selectors import (
    account_anomalies,
    account_subscriptions,
    account_summary,
    forecast_history,
)
from apps.transactions.serializers import AnomalyFlagSerializer, SubscriptionSerializer

DEFAULT_HORIZON_DAYS = 30
MAX_HORIZON_DAYS = 365


class AccountScopedView(APIView):
    def get_account(self, account_id) -> Account:
        return get_object_or_404(Account, pk=account_id)


class AccountSummaryView(AccountScopedView):
    """Category breakdown and income against expense for one account."""

    def get(self, request, account_id):
        account = self.get_account(account_id)
        return Response(account_summary(account))


class AccountSubscriptionsView(AccountScopedView):
    """Recurring charges detected for one account."""

    def get(self, request, account_id):
        account = self.get_account(account_id)
        subscriptions = account_subscriptions(account)
        return Response(
            {
                "account_id": str(account.id),
                "count": subscriptions.count(),
                "results": SubscriptionSerializer(subscriptions, many=True).data,
            }
        )


class AccountAnomaliesView(AccountScopedView):
    """Transactions flagged as standing out from the usual pattern."""

    def get(self, request, account_id):
        account = self.get_account(account_id)
        flags = account_anomalies(account)
        kind = request.query_params.get("kind")
        if kind:
            flags = flags.filter(kind=kind)
        return Response(
            {
                "account_id": str(account.id),
                "count": flags.count(),
                "results": AnomalyFlagSerializer(flags, many=True).data,
            }
        )


class AccountForecastView(AccountScopedView):
    """Cash flow projection, produced by the ml service."""

    def get(self, request, account_id):
        account = self.get_account(account_id)
        horizon = self._horizon(request)
        history = forecast_history(account)

        try:
            prediction = MlClient().forecast(history, horizon)
        except MlServiceError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(
            {
                "account_id": str(account.id),
                "horizon_days": horizon,
                **prediction,
            }
        )

    def _horizon(self, request) -> int:
        raw = request.query_params.get("horizon_days", DEFAULT_HORIZON_DAYS)
        try:
            horizon = int(raw)
        except (TypeError, ValueError):
            return DEFAULT_HORIZON_DAYS
        return max(1, min(horizon, MAX_HORIZON_DAYS))
