from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("id", "account_name", "email", "full_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "gender", "job")
    ordering = ("id",)
    search_fields = ("account_name", "email", "full_name", "phone_number")

    fieldsets = (
        (None, {"fields": ("account_name", "email", "password")}),
        ("Personal info", {"fields": ("full_name", "gender", "job", "age", "address", "phone_number", "other_info")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("account_name", "email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")

# Register your models here.
