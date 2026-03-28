from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    FishSpecies,
    FishingLog,
    Hook,
    Line,
    Lure,
    Manufacturer,
    Reel,
    Rod,
)

User = get_user_model()


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ("id", "name", "official_url")


class TackleBaseSerializer(serializers.ModelSerializer):
    manufacturer = ManufacturerSerializer(read_only=True)
    manufacturer_id = serializers.PrimaryKeyRelatedField(
        source="manufacturer", queryset=Manufacturer.objects.all(), write_only=True
    )

    class Meta:
        fields = ("id", "name", "manufacturer", "manufacturer_id", "official_url", "specs", "is_active")


class RodSerializer(TackleBaseSerializer):
    class Meta(TackleBaseSerializer.Meta):
        model = Rod


class ReelSerializer(TackleBaseSerializer):
    class Meta(TackleBaseSerializer.Meta):
        model = Reel


class LineSerializer(TackleBaseSerializer):
    class Meta(TackleBaseSerializer.Meta):
        model = Line


class HookSerializer(TackleBaseSerializer):
    class Meta(TackleBaseSerializer.Meta):
        model = Hook


class LureSerializer(TackleBaseSerializer):
    class Meta(TackleBaseSerializer.Meta):
        model = Lure


class FishSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FishSpecies
        fields = ("id", "name", "is_user_generated", "is_approved")
        read_only_fields = ("is_user_generated", "is_approved")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None
        # ユーザー追加は承認待ちとして登録。
        return FishSpecies.objects.create(
            name=validated_data["name"],
            is_user_generated=True,
            is_approved=False,
            created_by=user,
        )


class FishingLogSerializer(serializers.ModelSerializer):
    fish_species = FishSpeciesSerializer(many=True, read_only=True)
    fish_species_ids = serializers.PrimaryKeyRelatedField(
        source="fish_species", queryset=FishSpecies.objects.all(), many=True, write_only=True
    )
    rod_detail = RodSerializer(source="rod", read_only=True)
    reel_detail = ReelSerializer(source="reel", read_only=True)
    line_detail = LineSerializer(source="line", read_only=True)
    hook_detail = HookSerializer(source="hook", read_only=True)
    lure_detail = LureSerializer(source="lure", read_only=True)

    class Meta:
        model = FishingLog
        fields = (
            "id",
            "date",
            "time",
            "weather",
            "air_temperature",
            "water_temperature",
            "fish_species",
            "fish_species_ids",
            "size_value",
            "size_unit",
            "photo",
            "address",
            "latitude",
            "longitude",
            "rod",
            "rod_detail",
            "reel",
            "reel_detail",
            "line",
            "line_detail",
            "hook",
            "hook_detail",
            "lure",
            "lure_detail",
            "memo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        # 新規作成時のみ必須チェック。更新時は部分更新を許容。
        if self.instance is None:
            if not attrs.get("date"):
                raise serializers.ValidationError({"date": "日付は必須です。"})
            if not attrs.get("time"):
                raise serializers.ValidationError({"time": "時刻は必須です。"})
            if not attrs.get("fish_species"):
                raise serializers.ValidationError({"fish_species_ids": "魚種は必須です。"})
        size_value = attrs.get("size_value")
        size_unit = attrs.get("size_unit")
        if size_value and not size_unit:
            raise serializers.ValidationError({"size_unit": "サイズ単位を指定してください。"})
        return attrs

    def create(self, validated_data):
        fish_species = validated_data.pop("fish_species", [])
        user = self.context["request"].user
        # 先にログを作り、M2M を後からセットする。
        log = FishingLog.objects.create(user=user, **validated_data)
        log.fish_species.set(fish_species)
        return log
