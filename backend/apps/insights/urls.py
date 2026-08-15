"""Routes for the account insight endpoints."""

from django.urls import path

from apps.insights.views import (
    AccountAnomaliesView,
    AccountForecastView,
    AccountSubscriptionsView,
    AccountSummaryView,
)

urlpatterns = [
    path(
        "accounts/<uuid:account_id>/summary/",
        AccountSummaryView.as_view(),
        name="account-summary",
    ),
    path(
        "accounts/<uuid:account_id>/subscriptions/",
        AccountSubscriptionsView.as_view(),
        name="account-subscriptions",
    ),
    path(
        "accounts/<uuid:account_id>/anomalies/",
        AccountAnomaliesView.as_view(),
        name="account-anomalies",
    ),
    path(
        "accounts/<uuid:account_id>/forecast/",
        AccountForecastView.as_view(),
        name="account-forecast",
    ),
]
