from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import FishSpecies, FishingLog, Hook, Line, Lure, Manufacturer, Reel, Rod
from .serializers import (
    FishSpeciesSerializer,
    FishingLogSerializer,
    HookSerializer,
    LineSerializer,
    LureSerializer,
    ManufacturerSerializer,
    ReelSerializer,
    RodSerializer,
)


class SearchableViewSet(viewsets.ModelViewSet):
    search_fields = ("name",)

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.query_params.get("q")
        if q:
            # 軽量な部分一致検索でUIの検索ボックスと直結。
            queryset = queryset.filter(name__icontains=q)
        manufacturer_id = self.request.query_params.get("manufacturer_id")
        if manufacturer_id and hasattr(queryset.model, "manufacturer_id"):
            queryset = queryset.filter(manufacturer_id=manufacturer_id)
        return queryset


class ManufacturerViewSet(SearchableViewSet):
    queryset = Manufacturer.objects.all().order_by("name") # order_byはUIでの表示順を安定させるため。DBのID順は削除や追加で変わる可能性がある。 
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAuthenticated]


class RodViewSet(SearchableViewSet):
    queryset = Rod.objects.filter(is_active=True).select_related("manufacturer").order_by("name")
    serializer_class = RodSerializer
    permission_classes = [IsAuthenticated]


class ReelViewSet(SearchableViewSet):
    queryset = Reel.objects.filter(is_active=True).select_related("manufacturer").order_by("name")
    serializer_class = ReelSerializer
    permission_classes = [IsAuthenticated]


class LineViewSet(SearchableViewSet):
    queryset = Line.objects.filter(is_active=True).select_related("manufacturer").order_by("name")
    serializer_class = LineSerializer
    permission_classes = [IsAuthenticated]


class HookViewSet(SearchableViewSet):
    queryset = Hook.objects.filter(is_active=True).select_related("manufacturer").order_by("name")
    serializer_class = HookSerializer
    permission_classes = [IsAuthenticated]


class LureViewSet(SearchableViewSet):
    queryset = Lure.objects.filter(is_active=True).select_related("manufacturer").order_by("name")
    serializer_class = LureSerializer
    permission_classes = [IsAuthenticated]


class FishSpeciesViewSet(SearchableViewSet):
    queryset = FishSpecies.objects.filter(is_approved=True).order_by("name")
    serializer_class = FishSpeciesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        include_pending = self.request.query_params.get("include_pending")
        if include_pending == "1":
            # 管理/検証用に承認待ちも表示できるようにする。
            queryset = FishSpecies.objects.all().order_by("name")
        return queryset


class FishingLogViewSet(viewsets.ModelViewSet):
    serializer_class = FishingLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            FishingLog.objects.filter(user=self.request.user)
            # タックル詳細 + メーカーをまとめて取得してN+1を回避。
            .select_related(
                "rod",
                "rod__manufacturer",
                "reel",
                "reel__manufacturer",
                "line",
                "line__manufacturer",
                "hook",
                "hook__manufacturer",
                "lure",
                "lure__manufacturer",
            )
            .prefetch_related("fish_species")
        )
