from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FishSpeciesViewSet,
    FishingLogViewSet,
    HookViewSet,
    LineViewSet,
    LureViewSet,
    ManufacturerViewSet,
    ReelViewSet,
    RodViewSet,
)

router = DefaultRouter()
router.register(r"manufacturers", ManufacturerViewSet, basename="manufacturers")
router.register(r"rods", RodViewSet, basename="rods")
router.register(r"reels", ReelViewSet, basename="reels")
router.register(r"lines", LineViewSet, basename="lines")
router.register(r"hooks", HookViewSet, basename="hooks")
router.register(r"lures", LureViewSet, basename="lures")
router.register(r"fish-species", FishSpeciesViewSet, basename="fish-species")
router.register(r"fishing-logs", FishingLogViewSet, basename="fishing-logs")

urlpatterns = [
    path("", include(router.urls)),
]
