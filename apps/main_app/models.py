from django.conf import settings
from django.db import models


class Manufacturer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    official_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return self.name


class TackleBase(models.Model):
    # 共通タックル情報。スクレイピング結果を柔軟に保持するため specs はJSONにしている。
    name = models.CharField(max_length=200)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name="%(class)ss")
    official_url = models.URLField(blank=True)
    specs = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.manufacturer})"


class Rod(TackleBase):
    pass


class Reel(TackleBase):
    pass


class Line(TackleBase):
    pass


class Hook(TackleBase):
    pass


class Lure(TackleBase):
    pass


class ScrapeSource(models.Model):
    class Category(models.TextChoices):
        ROD = "rod", "ロッド"
        REEL = "reel", "リール"
        LINE = "line", "ライン"
        HOOK = "hook", "針"
        LURE = "lure", "ルアー"

    class Frequency(models.TextChoices):
        HOURLY = "hourly", "毎時"
        DAILY = "daily", "毎日"
        WEEKLY = "weekly", "毎週"
        MONTHLY = "monthly", "毎月"

    class Parser(models.TextChoices):
        GENERIC_LINKS = "generic_links", "汎用リンク抽出"
        SITEMAP = "sitemap", "サイトマップ"

    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name="scrape_sources")
    category = models.CharField(max_length=10, choices=Category.choices)
    # list_url は製品一覧や sitemap のURLを想定。URL不明時は空で保持して後から追加可能にする。
    list_url = models.URLField(blank=True, null=True)
    parser = models.CharField(max_length=30, choices=Parser.choices, default=Parser.GENERIC_LINKS)
    # メーカー別のHTML構造に対応するための追加設定（未指定なら汎用抽出）。
    link_selector = models.CharField(max_length=200, blank=True)
    link_allow_pattern = models.CharField(max_length=200, blank=True)
    link_deny_pattern = models.CharField(max_length=200, blank=True)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.WEEKLY)
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("manufacturer", "category", "list_url")

    def __str__(self) -> str:
        return f"{self.get_category_display()} {self.manufacturer.name}"


class FishSpecies(models.Model):
    # ユーザー自由入力の魚種は承認制で扱えるようにフラグを保持。
    name = models.CharField(max_length=100)
    is_user_generated = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fish_species_created",
    )
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("name", "is_user_generated")
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class FishingLog(models.Model):
    class SizeUnit(models.TextChoices):
        CM = "cm", "cm"
        KG = "kg", "kg"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fishing_logs")
    date = models.DateField()
    time = models.TimeField()
    weather = models.CharField(max_length=50, blank=True)
    air_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    water_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # 魚種は複数選択可能。
    fish_species = models.ManyToManyField(FishSpecies, related_name="fishing_logs")
    size_value = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    size_unit = models.CharField(max_length=2, choices=SizeUnit.choices, blank=True)
    photo = models.ImageField(upload_to="fishing_logs/photos/", blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # タックルは任意入力。削除時にログを壊さないよう SET_NULL。
    rod = models.ForeignKey(Rod, on_delete=models.SET_NULL, null=True, blank=True)
    reel = models.ForeignKey(Reel, on_delete=models.SET_NULL, null=True, blank=True)
    line = models.ForeignKey(Line, on_delete=models.SET_NULL, null=True, blank=True)
    hook = models.ForeignKey(Hook, on_delete=models.SET_NULL, null=True, blank=True)
    lure = models.ForeignKey(Lure, on_delete=models.SET_NULL, null=True, blank=True)
    memo = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time", "-id"]

    def __str__(self) -> str:
        return f"{self.user_id} {self.date} {self.time}"
