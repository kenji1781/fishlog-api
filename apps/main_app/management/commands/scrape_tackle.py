import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from main_app.models import Hook, Line, Lure, Manufacturer, Reel, Rod, ScrapeSource


TACKLE_MODEL_BY_CATEGORY = {
    ScrapeSource.Category.ROD: Rod,
    ScrapeSource.Category.REEL: Reel,
    ScrapeSource.Category.LINE: Line,
    ScrapeSource.Category.HOOK: Hook,
    ScrapeSource.Category.LURE: Lure,
}


class Command(BaseCommand):
    help = "Scrape tackle products from official manufacturer sites."

    def add_arguments(self, parser):
        parser.add_argument("--frequency", choices=[c for c, _ in ScrapeSource.Frequency.choices])
        parser.add_argument("--category", choices=[c for c, _ in ScrapeSource.Category.choices])
        parser.add_argument("--manufacturer")
        parser.add_argument("--seed", action="store_true", help="Seed initial manufacturers and scrape sources.")
        parser.add_argument("--limit", type=int, default=200)
        parser.add_argument("--sleep", type=float, default=1.0)

    def handle(self, *args, **options):
        if options["seed"]:
            self._seed_sources()

        frequency = options.get("frequency")
        sources = ScrapeSource.objects.filter(is_active=True).exclude(list_url__isnull=True).exclude(list_url="")
        if frequency:
            sources = sources.filter(frequency=frequency)
        if options.get("category"):
            sources = sources.filter(category=options["category"])
        if options.get("manufacturer"):
            sources = sources.filter(manufacturer__name__icontains=options["manufacturer"])

        for source in sources:
            if not source.list_url:
                continue
            if not self._is_allowed_by_robots(source.list_url):
                # robots.txt で拒否される場合はスキップ（規約遵守）。
                self.stdout.write(self.style.WARNING(f"SKIP robots: {source.list_url}"))
                continue

            self.stdout.write(f"Scraping: {source.list_url}")
            try:
                items = self._scrape(source, limit=options["limit"])
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"Failed: {source.list_url} ({exc})"))
                continue

            self._upsert_items(source, items)
            source.last_run_at = timezone.now()
            source.save(update_fields=["last_run_at"])
            time.sleep(options["sleep"])

    def _seed_sources(self):
        manufacturer_seed = [
            "SHIMANO",
            "DAIWA",
            "Megabass",
            "Major Craft",
            "Yamaga Blanks",
            "Nissin",
            "Gamakatsu",
            "Olympic",
            "Evergreen",
            "Palms",
            "Zenaq",
            "Tiemco",
            "Apia",
            "Breaden",
            "AIMS",
            "G-Craft",
            "Tailwalk",
            "Alpha Tackle",
            "M-on",
            "Gouki",
            "Fishman",
            "Zenith",
            "Truth Japan",
            "Carpenter",
            "Deps",
            "Gan Craft",
            "Raid Japan",
            "Nories",
            "Abu Garcia",
            "Okuma",
            "Penn",
            "Accurate",
            "Avet",
            "Van Staal",
            "Maxel",
            "Kureha",
            "Varivas",
            "Sunline",
            "YGK X-Braid",
            "Duel",
            "Morris",
            "Yamato Tegusu",
            "Line System",
            "Jackall",
            "Rapala",
            "Yamashita",
            "O.S.P",
            "Imakatsu",
            "Issei",
            "Bassday",
            "Zipbaits",
            "Hide Up",
            "Geecrack",
            "Bottom Up",
            "Engine",
            "Lucky Craft",
            "Gary Yamamoto",
            "Berkley",
            "Strike King",
            "Zoom",
            "Madness",
            "ima",
            "Jackson",
            "Blue Blue",
            "Tackle House",
            "Jado",
            "Jumprize",
            "Mangrove Studio",
            "Longin",
            "Coreman",
            "Signal",
            "INX.label",
            "Adusta",
            "Arkitect",
            "Squid Mania",
            "Kanji",
            "Harimitsu",
            "Valleyhill",
            "Marukyu",
            "Yamaria",
            "Ecogear",
            "Ocean Ruler",
            "Smith",
            "Owner",
            "Katsuichi",
        ]

        source_seed = [
            ("SHIMANO", "https://fish.shimano.com/ja-JP/product.html", ScrapeSource.Category.ROD, "", ""),
            ("SHIMANO", "https://fish.shimano.com/ja-JP/product.html", ScrapeSource.Category.REEL, "", ""),
            ("SHIMANO", "https://fish.shimano.com/ja-JP/product.html", ScrapeSource.Category.LINE, "", ""),
            ("SHIMANO", "https://fish.shimano.com/ja-JP/product.html", ScrapeSource.Category.LURE, "", ""),
            ("DAIWA", "https://www.daiwa.com/jp/product/productlist", ScrapeSource.Category.ROD, "", ""),
            ("DAIWA", "https://www.daiwa.com/jp/product/productlist", ScrapeSource.Category.REEL, "", ""),
            ("DAIWA", "https://www.daiwa.com/jp/product/productlist", ScrapeSource.Category.LINE, "", ""),
            ("Gamakatsu", "https://www.gamakatsu.co.jp/", ScrapeSource.Category.HOOK, "", ""),
            ("Owner", "https://www.ownerhooks.com/", ScrapeSource.Category.HOOK, "", ""),
            ("Sunline", "https://sunline.co.jp/", ScrapeSource.Category.LINE, "", ""),
            ("YGK X-Braid", "https://xbraidygk.co.jp/", ScrapeSource.Category.LINE, "", ""),
            ("Megabass", "https://megabass.co.jp/", ScrapeSource.Category.LURE, "", ""),
            ("Evergreen", "https://www.evergreen-fishing.com/products", ScrapeSource.Category.LURE, "", ""),
            ("DUO", "https://www.duo-international.com/", ScrapeSource.Category.LURE, "", ""),
        ]

        # seedは一括トランザクションで行い、途中失敗時の中途半端を防ぐ。
        with transaction.atomic():
            for name in manufacturer_seed:
                Manufacturer.objects.get_or_create(name=name)

            for name, url, category, allow_pattern, deny_pattern in source_seed:
                manufacturer, _ = Manufacturer.objects.get_or_create(name=name, defaults={"official_url": url})
                if not manufacturer.official_url:
                    manufacturer.official_url = url
                    manufacturer.save(update_fields=["official_url"])
                ScrapeSource.objects.get_or_create(
                    manufacturer=manufacturer,
                    category=category,
                    list_url=url,
                    defaults={
                        "link_allow_pattern": allow_pattern,
                        "link_deny_pattern": deny_pattern,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Seeded manufacturers and scrape sources."))

    def _is_allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        parser = RobotFileParser()
        try:
            parser.set_url(robots_url)
            parser.read()
            return parser.can_fetch("*", url)
        except Exception:
            return False

    def _scrape(self, source: ScrapeSource, limit: int = 200) -> list[tuple[str, str]]:
        # parser種別で処理を切り替える（サイトマップ or 汎用リンク）。
        if source.parser == ScrapeSource.Parser.SITEMAP:
            return self._scrape_sitemap(source.list_url, source, limit)
        return self._scrape_generic_links(source.list_url, source, limit)

    def _scrape_sitemap(self, url: str, source: ScrapeSource, limit: int) -> list[tuple[str, str]]:
        response = requests.get(url, timeout=20, headers={"User-Agent": "fishlog-bot/0.1"})
        response.raise_for_status()
        root = ET.fromstring(response.text)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        items = []
        seen = set()
        for loc in root.findall(".//ns:loc", namespace):
            href = loc.text.strip()
            if not self._is_allowed_link(href, source):
                continue
            # URL末尾から仮の製品名を作る（後で手動整備する想定）。
            name = href.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").strip()
            if not name:
                continue
            key = (name, href)
            if key in seen:
                continue
            seen.add(key)
            items.append((name, href))
            if len(items) >= limit:
                break
        return items

    def _scrape_generic_links(self, url: str, source: ScrapeSource, limit: int) -> list[tuple[str, str]]:
        response = requests.get(url, timeout=20, headers={"User-Agent": "fishlog-bot/0.1"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items = []
        seen = set()
        # selectorが指定されていれば優先。なければ全リンクから抽出。
        selector = source.link_selector or "a[href]"
        for a in soup.select(selector):
            name = a.get_text(strip=True)
            href = a.get("href")
            if not name or len(name) < 2 or not href:
                continue
            if not self._is_allowed_link(href, source):
                continue
            key = (name, href)
            if key in seen:
                continue
            seen.add(key)
            items.append((name, href))
            if len(items) >= limit:
                break
        return items

    def _is_allowed_link(self, href: str, source: ScrapeSource) -> bool:
        # 正規表現で対象リンクを絞り込み（精度UP用）。
        if source.link_allow_pattern:
            if not re.search(source.link_allow_pattern, href):
                return False
        if source.link_deny_pattern:
            if re.search(source.link_deny_pattern, href):
                return False
        return True

    def _upsert_items(self, source: ScrapeSource, items: list[tuple[str, str]]):
        model = TACKLE_MODEL_BY_CATEGORY[source.category]
        created = 0
        for name, href in items:
            obj, was_created = model.objects.get_or_create(
                name=name,
                manufacturer=source.manufacturer,
                defaults={"official_url": href},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} items for {source.manufacturer.name}"))
