from django.contrib import admin

from .models import (
    FishSpecies,
    FishingLog,
    Hook,
    Line,
    Lure,
    Manufacturer,
    Reel,
    Rod,
    ScrapeSource,
)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "official_url")
    search_fields = ("name",)


@admin.register(Rod, Reel, Line, Hook, Lure)
class TackleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "manufacturer", "official_url", "is_active")
    list_filter = ("manufacturer", "is_active")
    search_fields = ("name",)


@admin.register(ScrapeSource)
class ScrapeSourceAdmin(admin.ModelAdmin):
    list_display = ("id", "manufacturer", "category", "frequency", "is_active", "last_run_at")
    list_filter = ("category", "frequency", "is_active", "parser")
    search_fields = ("manufacturer__name", "list_url")


@admin.register(FishSpecies)
class FishSpeciesAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_user_generated", "is_approved", "created_by", "created_at")
    list_filter = ("is_user_generated", "is_approved")
    search_fields = ("name",)


@admin.register(FishingLog)
class FishingLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "date", "time")
    list_filter = ("date",)
    search_fields = ("user__email", "user__account_name", "address", "memo")

# Register your models here.
