"""API router wiring every resource under /api."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import AccountViewSet
from apps.transactions.views import (
    AnomalyFlagViewSet,
    BudgetViewSet,
    CategoryViewSet,
    MerchantViewSet,
    SubscriptionViewSet,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("categories", CategoryViewSet, basename="category")
router.register("merchants", MerchantViewSet, basename="merchant")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("budgets", BudgetViewSet, basename="budget")
router.register("anomaly-flags", AnomalyFlagViewSet, basename="anomaly-flag")

urlpatterns = [
    path("", include(router.urls)),
]
